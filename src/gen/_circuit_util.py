from typing import Union, Literal, Tuple, List, FrozenSet, Set

import stim

from gen._builder import Builder
from gen._flow import PauliString
from gen._noise import NoiseModel, NoiseRule
from gen._patch import Patch
from gen._util import sorted_complex


def _observables(
    *,
    patch: Patch,
    obs_x: PauliString,
    obs_z: PauliString,
    basis: Union[Literal['X', 'Z', 'XZ'], str],
) -> Tuple[List[PauliString], FrozenSet[complex]]:
    assert obs_x.anticommutes(obs_z)
    if basis == 'X':
        observables = [obs_x]
        immune = frozenset()
    elif basis == 'Z':
        observables = [obs_z]
        immune = frozenset()
    elif basis == 'XZ':
        r = max(q.real for q in patch.data_set)
        i = max(q.imag for q in patch.data_set)
        ancilla = r + i*1j + 1
        immune = frozenset([ancilla])
        observables = [
            obs_x * PauliString({ancilla: 'X'}),
            obs_z * PauliString({ancilla: 'Z'}),
        ]
    else:
        raise NotImplementedError(f'{basis=}')
    return observables, immune


def make_phenomenological_circuit_for_stabilizer_code(
        *,
        patch: Patch,
        noise: NoiseRule,
        obs_x: PauliString,
        obs_z: PauliString,
        basis: Union[Literal['X', 'Z', 'XZ'], str],
        rounds: int,
) -> stim.Circuit:
    observables, immune = _observables(patch=patch, obs_x=obs_x, obs_z=obs_z, basis=basis)
    builder = Builder.for_qubits(patch.data_set | immune)

    for k, obs in enumerate(observables):
        builder.measure_pauli_product(q2b=obs.qubits, key=f'OBS_START{k}')
        builder.obs_include([f'OBS_START{k}'], obs_index=k)
    builder.measure_patch(patch, save_layer='init')
    builder.tick()

    loop = builder.fork()
    loop.measure_patch(patch, save_layer='loop', cmp_layer='init')
    loop.shift_coords(dt=1)
    loop.tick()
    noise_model = NoiseModel(
        tick_noise=NoiseRule(after=noise.after),
        any_measurement_rule=NoiseRule(flip_result=noise.flip_result, after={}),
        any_clifford_1q_rule=NoiseRule(after={}),
        any_clifford_2q_rule=NoiseRule(after={}),
        allow_multiple_uses_of_a_qubit_in_one_tick=True,
    )
    noisy_loop = noise_model.noisy_circuit(
        loop.circuit,
        immune_qubits={builder.q2i[q] for q in immune},
    )
    builder.circuit += noisy_loop * rounds

    builder.measure_patch(patch, save_layer='end', cmp_layer='loop')
    for k, obs in enumerate(observables):
        builder.measure_pauli_product(q2b=obs.qubits, key=f'OBS_END{k}')
        builder.obs_include([f'OBS_END{k}'], obs_index=k)

    return builder.circuit


def make_code_capacity_circuit_for_stabilizer_code(
        *,
        patch: Patch,
        noise: NoiseRule,
        obs_x: PauliString,
        obs_z: PauliString,
        basis: str,
) -> stim.Circuit:
    assert noise.flip_result == 0
    observables, immune = _observables(patch=patch, obs_x=obs_x, obs_z=obs_z, basis=basis)
    builder = Builder.for_qubits(patch.data_set | immune)

    for k, obs in enumerate(observables):
        builder.measure_pauli_product(q2b=obs.qubits, key=f'OBS_START{k}')
        builder.obs_include([f'OBS_START{k}'], obs_index=k)
    builder.measure_patch(patch, save_layer='init')
    builder.tick()

    for k, p in noise.after.items():
        builder.circuit.append(k, [builder.q2i[q] for q in sorted_complex(patch.data_set)], p)
    builder.tick()

    builder.measure_patch(patch, save_layer='end', cmp_layer='init')
    for k, obs in enumerate(observables):
        builder.measure_pauli_product(q2b=obs.qubits, key=f'OBS_END{k}')
        builder.obs_include([f'OBS_END{k}'], obs_index=k)

    return builder.circuit


def gates_used_by_circuit(circuit: stim.Circuit) -> Set[str]:
    """Determines gates used by a circuit, disambiguating MPP/feedback cases.

    MPP instructions are expanded into what they actually measure, such as
    "MXX" for MPP X1*X2 and "MXYZ" for MPP X4*Y5*Z7.

    Feedback instructions like `CX rec[-1] 0` become the gate "feedback".

    Sweep instructions like `CX sweep[2] 0` become the gate "sweep".
    """
    out = set()
    for instruction in circuit:
        if isinstance(instruction, stim.CircuitRepeatBlock):
            out |= gates_used_by_circuit(instruction.body_copy())

        elif instruction.name in ['CX', 'CY', 'CZ', 'XCZ', 'YCZ']:
            targets = instruction.targets_copy()
            for k in range(0, len(targets), 2):
                if targets[k].is_measurement_record_target or targets[k + 1].is_measurement_record_target:
                    out.add('feedback')
                elif targets[k].is_sweep_bit_target or targets[k + 1].is_sweep_bit_target:
                    out.add('sweep')
                else:
                    out.add(instruction.name)

        elif instruction.name == 'MPP':
            op = 'M'
            targets = instruction.targets_copy()
            is_continuing = True
            for t in targets:
                if t.is_combiner:
                    is_continuing = True
                    continue
                p = 'X' if t.is_x_target else 'Y' if t.is_y_target else 'Z' if t.is_z_target else '?'
                if is_continuing:
                    op += p
                    is_continuing = False
                else:
                    if op == 'MZ':
                        op = 'M'
                    out.add(op)
                    op = 'M' + p
            if op:
                if op == 'MZ':
                    op = 'M'
                out.add(op)

        else:
            out.add(instruction.name)

    return out
