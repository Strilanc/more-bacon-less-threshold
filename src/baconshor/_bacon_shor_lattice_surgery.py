from typing import List, Union, Dict, Callable, Set, Any, Optional

import sinter
import stim

import gen
from baconshor._bacon_shor import make_bacon_shor_patch


def _det(*, builder: gen.Builder, group: List[gen.Tile], layers: List[Any], include_data: bool = False):
    builder.detector(
        [
            gen.AtLayer(q, layer)
            for tile in group
            for layer in layers
            for q in (tile.used_set if include_data else [tile.measurement_qubit])
        ],
        pos=min([tile.measurement_qubit for tile in group], key=gen.complex_key),
    )


def _do_det_groups(*, builder: gen.Builder, patch: gen.Patch, basis: str, layers: List[Any], include_data: bool = False):
    groups = sinter.group_by(
        [tile for tile in patch.tiles if tile.basis == basis],
        key=lambda tile: tile.measurement_qubit.real if basis == 'X' else tile.measurement_qubit.imag,
    )
    for _, group in sorted(groups.items()):
        _det(builder=builder, group=group, layers=layers, include_data=include_data)


def _run_round(*,
               builder: gen.Builder,
               patch: gen.Patch,
               save_layer: Any):
    for tile in patch.tiles:
        m = tile.measurement_qubit
        if tile.basis == 'X' and m.real % 2 == 0.5:
            builder.measure_pauli_product(xs=tile.data_set, key=gen.AtLayer(m, save_layer))
    builder.tick()
    for tile in patch.tiles:
        m = tile.measurement_qubit
        if tile.basis == 'X' and m.real % 2 == 1.5:
            builder.measure_pauli_product(xs=tile.data_set, key=gen.AtLayer(m, save_layer))
    builder.tick()
    for tile in patch.tiles:
        m = tile.measurement_qubit
        if tile.basis == 'Z' and m.imag % 2 == 0.5:
            builder.measure_pauli_product(zs=tile.data_set, key=gen.AtLayer(m, save_layer))
    builder.tick()
    for tile in patch.tiles:
        m = tile.measurement_qubit
        if tile.basis == 'Z' and m.imag % 2 == 1.5:
            builder.measure_pauli_product(zs=tile.data_set, key=gen.AtLayer(m, save_layer))


def make_bacon_shor_xx_lattice_surgery_circuit(
        *,
        width: int,
        height: int,
        basis: str,
        rounds: int,
) -> stim.Circuit:
    left_patch = make_bacon_shor_patch(width=width, height=height).patch
    right_patch = left_patch.after_coordinate_transform(lambda q: q + width)
    merged_patch = make_bacon_shor_patch(width=width * 2, height=height).patch
    split_patch = gen.Patch(left_patch.tiles + right_patch.tiles)
    x1 = gen.PauliString({q: 'X' for q in merged_patch.data_set if q.real == width - 1})
    x2 = gen.PauliString({q: 'X' for q in merged_patch.data_set if q.real == width})
    zz = gen.PauliString({q: 'Z' for q in merged_patch.data_set if q.imag == 0})
    assert x1.anticommutes(zz)
    assert x2.anticommutes(zz)
    assert not x1.anticommutes(x2)
    assert split_patch.data_set == merged_patch.data_set

    builder = gen.Builder.for_qubits(merged_patch.data_set)

    builder.gate(f'R{basis}', merged_patch.data_set)
    builder.tick()

    _run_round(builder=builder, patch=split_patch, save_layer='init')
    if basis == 'X':
        for tile in split_patch.tiles:
            if tile.basis == 'X':
                m = tile.measurement_qubit
                builder.detector([gen.AtLayer(m, 'init')], pos=m)
    else:
        _do_det_groups(builder=builder, patch=left_patch, basis=basis, layers=['init'])
        _do_det_groups(builder=builder, patch=right_patch, basis=basis, layers=['init'])
    builder.shift_coords(dt=1)
    builder.tick()

    _run_round(builder=builder, patch=merged_patch, save_layer='stitch')
    _do_det_groups(builder=builder, patch=split_patch, basis='X', layers=['init', 'stitch'])
    _do_det_groups(builder=builder, patch=split_patch, basis='Z', layers=['init', 'stitch'])
    if basis == 'X':
        builder.obs_include(
            [gen.AtLayer(tile.measurement_qubit, 'stitch') for tile in merged_patch.tiles if tile.measurement_qubit.real == width - 0.5],
            obs_index=2,
        )
    builder.shift_coords(dt=1)
    builder.tick()

    loop = builder.fork()
    _run_round(builder=loop, patch=merged_patch, save_layer='loop')
    _do_det_groups(builder=loop, patch=merged_patch, basis='X', layers=['loop', 'stitch'])
    _do_det_groups(builder=loop, patch=merged_patch, basis='Z', layers=['loop', 'stitch'])
    loop.shift_coords(dt=1)
    loop.tick()
    builder.circuit += loop.circuit * (rounds - 1)

    _run_round(builder=builder, patch=split_patch, save_layer='end')
    _do_det_groups(builder=builder, patch=split_patch, basis='X', layers=['end', 'loop'])
    _do_det_groups(builder=builder, patch=left_patch, basis='Z', layers=['end', 'loop'])
    _do_det_groups(builder=builder, patch=right_patch, basis='Z', layers=['end', 'loop'])
    builder.shift_coords(dt=1)
    builder.tick()

    builder.measure(merged_patch.data_set, basis=basis, save_layer='end')
    if basis == 'X':
        _do_det_groups(builder=builder, patch=split_patch, basis='X', layers=['end'], include_data=True)
        builder.obs_include(
            [gen.AtLayer(q, 'end') for q in x1.qubits],
            obs_index=0,
        )
        builder.obs_include(
            [gen.AtLayer(q, 'end') for q in x2.qubits],
            obs_index=1,
        )
    else:
        for tile in split_patch.tiles:
            if tile.basis == 'Z':
                builder.detector([gen.AtLayer(q, 'end') for q in tile.used_set], pos=tile.measurement_qubit)
        builder.obs_include(
            [gen.AtLayer(q, 'end') for q in zz.qubits],
            obs_index=0,
        )

    return builder.circuit


def _bacon_shor_xx_lattice_surgery_circuit_chunks_from_params(params: gen.CircuitBuildParams) -> List[Union[gen.Chunk, gen.ChunkLoop]]:
    circuit = make_bacon_shor_xx_lattice_surgery_circuit(
        width=params.diameter,
        height=params.diameter,
        basis=params.custom['b'],
        rounds=params.rounds,
    )
    return [gen.Chunk(
        circuit=circuit,
        q2i={r + 1j*i: k for k, (r, i) in circuit.get_final_qubit_coordinates().items()},
        flows=[],
    )]


def make_bacon_shor_lattice_surgery_constructions() -> Dict[str, Callable[[gen.CircuitBuildParams], List[Union[gen.Chunk, gen.ChunkLoop]]]]:
    return {
        'bacon_shor_xx_surgery': _bacon_shor_xx_lattice_surgery_circuit_chunks_from_params,
    }
