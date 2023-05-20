from typing import List, Union, Dict, Callable, Set

import sinter
import stim

import gen
from baconshor._bacon_shor import make_bacon_shor_patch


def is_parity_measurement_active(
        *,
        divider_index: int,
        time_step: int,
        space_d: int,
        time_d: int,
        phase1: int,
        phase2: int,
) -> bool:
    phases = [phase1, phase2]

    assert divider_index >= 0
    divider_index += 1
    while divider_index > 0:
        if divider_index % space_d != 0:
            return True
        divider_index //= space_d
        time_step //= time_d

        if time_step % 4 != phases[divider_index % 2]:
            return False
        time_step //= 4

    return False


def fractal_bacon_shor_detector_ranges(
        *,
        line_top_left: complex,
        line_dir: complex,
        span: int,
        line_cuts_inplace_edit: Set[complex],
) -> List[List[complex]]:
    result = []

    start = 0
    while start < span:
        end = start
        vs = []
        while end < span:
            v = line_top_left + 0.5 + 0.5j + end * line_dir
            vs.append(v - 0.5*line_dir)
            end += 1
            if v not in line_cuts_inplace_edit:
                break
            line_cuts_inplace_edit.discard(v)
        result.append(vs)
        start = end

    return result


def do_x_measures(
        *,
        patch: gen.Patch,
        z_cuts: Set[complex],
        x_cuts: Set[complex],
        builder: gen.Builder,
        last_usage_x: Dict[int, int],
        height: int,
        step: int,
        is_active_func: Callable[[gen.Tile], bool],
):
    used_xs = set()
    for tile in patch.tiles:
        m = tile.measurement_qubit
        if tile.basis == 'X' and is_active_func(tile):
            builder.measure_pauli_product(xs=tile.data_set, key=gen.AtLayer(m, f'x_round{step}'))
            z_cuts.add(m - 0.5j)
            z_cuts.add(m + 0.5j)
            used_xs.add(m.real - 0.5)

    for x in used_xs:
        prev_step = last_usage_x.get(x)
        last_usage_x[x] = step

        vvs = fractal_bacon_shor_detector_ranges(
            line_top_left=x,
            line_dir=1j,
            span=height,
            line_cuts_inplace_edit=x_cuts,
        )

        if prev_step is None:
            continue
        if prev_step == 'init':
            cmp = [step]
        else:
            cmp = [prev_step, step]

        for vs in vvs:
            builder.detector([
                gen.AtLayer(v, f'x_round{t}')
                for v in vs
                for t in cmp
            ], pos=min(vs, key=gen.complex_key), extra_coords=[1])
    builder.shift_coords(dt=1)
    builder.tick()


def do_z_measures(
        *,
        patch: gen.Patch,
        z_cuts: Set[complex],
        x_cuts: Set[complex],
        builder: gen.Builder,
        last_usage_z: Dict[int, int],
        width: int,
        step: int,
        is_active_func: Callable[[gen.Tile], bool],
):
    used_zs = set()
    for tile in patch.tiles:
        m = tile.measurement_qubit
        if tile.basis == 'Z' and is_active_func(tile):
            builder.measure_pauli_product(zs=tile.data_set, key=gen.AtLayer(m, f'z_round{step}'))
            used_zs.add(m.imag - 0.5)
            x_cuts.add(m - 0.5)
            x_cuts.add(m + 0.5)

    for z in used_zs:
        prev_step = last_usage_z.get(z)
        last_usage_z[z] = step

        vvs = fractal_bacon_shor_detector_ranges(
            line_top_left=z*1j,
            line_dir=1,
            span=width,
            line_cuts_inplace_edit=z_cuts,
        )

        if prev_step is None:
            continue
        if prev_step == 'init':
            cmp = [step]
        else:
            cmp = [prev_step, step]

        for vs in vvs:
            builder.detector([
                gen.AtLayer(v, f'z_round{t}')
                for v in vs
                for t in cmp
            ], pos=min(vs, key=gen.complex_key) + 10, extra_coords=[2])
    builder.shift_coords(dt=1)
    builder.tick()


def do_end_x_measures(
        *,
        patch: gen.Patch,
        x_cuts: Set[complex],
        builder: gen.Builder,
        last_usage_x: Dict[int, int],
        height: int,
):
    used_xs = set()
    for tile in patch.tiles:
        if tile.basis == 'X':
            used_xs.add(tile.measurement_qubit.real - 0.5)
    builder.measure(patch.data_set, basis='X', save_layer='end')
    builder.obs_include([gen.AtLayer(q, 'end') for q in patch.data_set if q.real == 0], obs_index=0)
    for x in used_xs:
        prev_step = last_usage_x.get(x)

        vvs = fractal_bacon_shor_detector_ranges(
            line_top_left=x,
            line_dir=1j,
            span=height,
            line_cuts_inplace_edit=x_cuts,
        )

        if prev_step is None:
            continue
        if prev_step == 'init':
            cmp = []
        else:
            cmp = [prev_step]

        for vs in vvs:
            builder.detector([
                gen.AtLayer(v, f'x_round{t}')
                for v in vs
                for t in cmp
            ] + [
                gen.AtLayer(v + d, f'end')
                for v in vs
                for d in [-0.5, +0.5]
            ], pos=min(vs, key=gen.complex_key), extra_coords=[1])


def do_end_z_measures(
        *,
        patch: gen.Patch,
        z_cuts: Set[complex],
        builder: gen.Builder,
        last_usage_z: Dict[int, int],
        width: int,
):
    used_zs = set()
    for tile in patch.tiles:
        if tile.basis == 'Z':
            used_zs.add(tile.measurement_qubit.imag - 0.5)
    builder.measure(patch.data_set, basis='Z', save_layer='end')
    builder.obs_include([gen.AtLayer(q, 'end') for q in patch.data_set if q.imag == 0], obs_index=0)
    for z in used_zs:
        prev_step = last_usage_z.get(z)

        vvs = fractal_bacon_shor_detector_ranges(
            line_top_left=z*1j,
            line_dir=1,
            span=width,
            line_cuts_inplace_edit=z_cuts,
        )

        if prev_step is None:
            continue
        if prev_step == 'init':
            cmp = []
        else:
            cmp = [prev_step]

        for vs in vvs:
            builder.detector([
                gen.AtLayer(v, f'z_round{t}')
                for v in vs
                for t in cmp
            ] + [
                gen.AtLayer(v + d, f'end')
                for v in vs
                for d in [-0.5j, +0.5j]
            ], pos=min(vs, key=gen.complex_key), extra_coords=[2])


def make_bacon_shor_fractal_circuit(
        *,
        width: int,
        height: int,
        rounds: int,
        basis: str,
        fractal_pitch: int,
        surgery_hold_factor: int,
) -> stim.Circuit:
    code = make_bacon_shor_patch(width=width, height=height)
    patch = code.patch

    x_cuts = set()
    z_cuts = set()
    last_usage_x = {x: 'init' for x in range(width)} if basis == 'X' else {}
    last_usage_z = {z: 'init' for z in range(height)} if basis == 'Z' else {}

    builder = gen.Builder.for_qubits(patch.data_set)
    builder.gate(f'R{basis}', patch.data_set)
    builder.tick()

    for step in range(rounds):
        for parity in [0.5, 1.5]:
            do_x_measures(
                patch=patch,
                z_cuts=z_cuts,
                x_cuts=x_cuts,
                builder=builder,
                last_usage_x=last_usage_x,
                height=height,
                step=step,
                is_active_func=lambda tile: tile.measurement_qubit.real % 2 == parity and is_parity_measurement_active(
                    divider_index=int(tile.ordered_data_qubits[0].real),
                    time_step=step,
                    space_d=fractal_pitch,
                    time_d=surgery_hold_factor,
                    phase1=0,
                    phase2=2,
                ),
            )
        for parity in [0.5, 1.5]:
            do_z_measures(
                patch=patch,
                z_cuts=z_cuts,
                x_cuts=x_cuts,
                builder=builder,
                last_usage_z=last_usage_z,
                width=width,
                step=step,
                is_active_func=lambda tile: tile.measurement_qubit.imag % 2 == parity and is_parity_measurement_active(
                    divider_index=int(tile.ordered_data_qubits[0].imag),
                    time_step=step,
                    space_d=fractal_pitch,
                    time_d=surgery_hold_factor,
                    phase1=1,
                    phase2=3,
                ),
            )

    if basis == 'X':
        do_end_x_measures(
            patch=patch,
            x_cuts=x_cuts,
            builder=builder,
            last_usage_x=last_usage_x,
            height=height,
        )
    elif basis == 'Z':
        do_end_z_measures(
            patch=patch,
            z_cuts=z_cuts,
            builder=builder,
            last_usage_z=last_usage_z,
            width=width,
        )
    else:
        raise NotImplementedError(f'{basis=}')

    return builder.circuit


def _fractal_bacon_shor_circuit_chunks_from_params(params: gen.CircuitBuildParams) -> List[Union[gen.Chunk, gen.ChunkLoop]]:
    circuit = make_bacon_shor_fractal_circuit(
        width=params.diameter,
        height=params.diameter,
        basis=params.custom['b'],
        rounds=params.rounds,
        fractal_pitch=params.custom['fractal_pitch'],
        surgery_hold_factor=params.custom['surgery_hold_factor'],
    )
    return [gen.Chunk(
        circuit=circuit,
        q2i={r + 1j*i: k for k, (r, i) in circuit.get_final_qubit_coordinates().items()},
        flows=[],
    )]


def make_fractal_bacon_shor_constructions() -> Dict[str, Callable[[gen.CircuitBuildParams], List[Union[gen.Chunk, gen.ChunkLoop]]]]:
    return {
        'fractal_bacon_shor': _fractal_bacon_shor_circuit_chunks_from_params,
    }
