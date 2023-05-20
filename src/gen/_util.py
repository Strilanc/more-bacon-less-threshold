import pathlib
from typing import List, Callable, Iterable, TypeVar, Any, Tuple, Dict, Union

import numpy as np
import stim

TItem = TypeVar('TItem')


def complex_key(c: complex) -> Any:
    return c.real != int(c.real), c.real, c.imag


def sorted_complex(
        values: Iterable[TItem],
        *,
        key: Callable[[TItem], Any] = lambda e: e) -> List[TItem]:
    return sorted(values, key=lambda e: complex_key(key(e)))


def not_nones(vs) -> List[Any]:
    return [v for v in vs if v is not None]


def stim_circuit_with_transformed_coords(
        circuit: stim.Circuit, transform: Callable[[complex], complex]
) -> stim.Circuit:
    """Returns an equivalent circuit, but with the qubit and detector position metadata modified.
    The "position" is assumed to be the first two coordinates. These are mapped to the real and
    imaginary values of a complex number which is then transformed.

    Note that `SHIFT_COORDS` instructions that modify the first two coordinates are not supported.
    This is because supporting them requires flattening loops, or promising that the given
    transformation is affine.

    Args:
        circuit: The circuit with qubits to reposition.
        transform: The transformation to apply to the positions. The positions are given one by one
            to this method, as complex numbers. The method returns the new complex number for the
            position.

    Returns:
        The transformed circuit.
    """
    result = stim.Circuit()
    for instruction in circuit:
        if isinstance(instruction, stim.CircuitInstruction):
            if instruction.name == "QUBIT_COORDS" or instruction.name == "DETECTOR":
                args = list(instruction.gate_args_copy())
                while len(args) < 2:
                    args.append(0)
                c = transform(args[0] + args[1] * 1j)
                args[0] = c.real
                args[1] = c.imag
                result.append(instruction.name, instruction.targets_copy(), args)
                continue
            if instruction.name == "SHIFT_COORDS":
                args = instruction.gate_args_copy()
                if any(args[:2]):
                    raise NotImplementedError(f"Shifting first two coords: {instruction=}")

        if isinstance(instruction, stim.CircuitRepeatBlock):
            result.append(
                stim.CircuitRepeatBlock(
                    repeat_count=instruction.repeat_count,
                    body=stim_circuit_with_transformed_coords(instruction.body_copy(), transform),
                )
            )
            continue

        result.append(instruction)
    return result


def stim_circuit_with_transformed_moments(
        circuit: stim.Circuit, *, moment_func: Callable[[stim.Circuit], stim.Circuit]
) -> stim.Circuit:
    """Applies a transformation to regions of a circuit separated by TICKs and blocks.

    For example, in this circuit:

        H 0
        X 0
        TICK

        H 1
        X 1
        REPEAT 100 {
            H 2
            X 2
        }
        H 3
        X 3

        TICK
        H 4
        X 4

    `moment_func` would be called five times, each time with one of the H and X instruction pairs.
    The result from the method would then be substituted into the circuit, replacing each of the H
    and X instruction pairs.

    Args:
        circuit: The circuit to return a transformed result of.
        moment_func: The transformation to apply to regions of the circuit. Returns a new circuit
            for the result.

    Returns:
        A transformed circuit.
    """

    result = stim.Circuit()
    current_moment = stim.Circuit()

    for instruction in circuit:
        if isinstance(instruction, stim.CircuitRepeatBlock):
            # Implicit tick at transition into REPEAT?
            if current_moment:
                result += moment_func(current_moment)
                current_moment.clear()

            transformed_body = stim_circuit_with_transformed_moments(
                instruction.body_copy(), moment_func=moment_func
            )
            result.append(
                stim.CircuitRepeatBlock(
                    repeat_count=instruction.repeat_count, body=transformed_body
                )
            )
        elif isinstance(instruction, stim.CircuitInstruction) and instruction.name == 'TICK':
            # Explicit tick. Process even if empty.
            result += moment_func(current_moment)
            result.append('TICK')
            current_moment.clear()
        else:
            current_moment.append(instruction)

    # Implicit tick at end of circuit?
    if current_moment:
        result += moment_func(current_moment)

    return result


def estimate_qubit_count_during_postselection(circuit: stim.Circuit) -> int:
    circuit = circuit.without_noise()
    start = 0
    end = 0
    for k, instruction in enumerate(circuit):
        if isinstance(instruction, stim.CircuitInstruction):
            if instruction.name == 'QUBIT_COORDS':
                start = k + 1
            elif instruction.name == 'DETECTOR':
                args = instruction.gate_args_copy()
                if len(args) >= 4 and args[3] == 999:
                    end = k + 1
    used_qubits = set()
    def process(sub_circuit: stim.Circuit):
        for inst in sub_circuit:
            if isinstance(inst, stim.CircuitRepeatBlock):
                process(inst.body_copy())
            else:
                for t in inst.targets_copy():
                    if t.is_qubit_target:
                        used_qubits.add(t.value)
    process(circuit[start:end])
    return len(used_qubits)


def write_file(path: Union[pathlib.Path, str], content: Any):
    with open(path, 'w') as f:
        print(content, file=f)
    print(f'wrote file://{pathlib.Path(path).absolute()}')


def count_ticks(circuit: stim.Circuit) -> int:
    total = 0
    for inst in circuit:
        if isinstance(inst, stim.CircuitRepeatBlock):
            total += inst.repeat_count * count_ticks(inst.body_copy())
        elif isinstance(inst, stim.CircuitInstruction):
            if inst.name == 'TICK':
                total += 1
        else:
            raise NotImplementedError(f'{inst=}')
    return total


def count_determined_measurements_in_circuit(circuit: stim.Circuit) -> int:
    """Simulates the circuit, counting how many measurements were determined.

    In most cases, for a quantum error correcting code, the result should be
    related to the number of detectors plus the number of observables declared
    in the circuit.
    """

    num_determined_measurements = 0
    sim = stim.TableauSimulator()
    n = circuit.num_qubits

    def run_block(block: stim.Circuit, reps: int):
        nonlocal num_determined_measurements
        for _ in range(reps):
            for inst in block:
                if isinstance(inst, stim.CircuitRepeatBlock):
                    run_block(inst.body_copy(), inst.repeat_count)
                elif inst.name == 'M' or inst.name == 'MR':
                    args = inst.gate_args_copy()
                    for t in inst.targets_copy():
                        assert t.is_qubit_target
                        known = sim.peek_z(t.value) != 0
                        num_determined_measurements += known
                        sim.do(stim.CircuitInstruction(inst.name, [t.value], args))
                elif inst.name == 'MX' or inst.name == 'MRX':
                    args = inst.gate_args_copy()
                    for t in inst.targets_copy():
                        assert t.is_qubit_target
                        known = sim.peek_x(t.value) != 0
                        num_determined_measurements += known
                        sim.do(stim.CircuitInstruction(inst.name, [t.value], args))
                elif inst.name == 'MY' or inst.name == 'MRY':
                    args = inst.gate_args_copy()
                    for t in inst.targets_copy():
                        assert t.is_qubit_target
                        known = sim.peek_y(t.value) != 0
                        num_determined_measurements += known
                        sim.do(stim.CircuitInstruction(inst.name, [t.value], args))
                elif inst.name == 'MPP':
                    args = inst.gate_args_copy()
                    targets = inst.targets_copy()
                    start = 0
                    while start < len(targets):
                        end = start + 1
                        while end < len(targets) and targets[end].is_combiner:
                            end += 2

                        p = stim.PauliString(n)
                        for t in targets[start:end:2]:
                            if t.is_x_target:
                                p[t.value] = 'X'
                            elif t.is_y_target:
                                p[t.value] = 'Y'
                            elif t.is_z_target:
                                p[t.value] = 'Z'
                            else:
                                raise NotImplementedError(f'{t=} {inst=}')

                        known = sim.peek_observable_expectation(p) != 0
                        num_determined_measurements += known
                        sim.do(stim.CircuitInstruction(inst.name, targets[start:end], args))

                        start = end
                else:
                    sim.do(inst)

    run_block(circuit, 1)
    return num_determined_measurements
