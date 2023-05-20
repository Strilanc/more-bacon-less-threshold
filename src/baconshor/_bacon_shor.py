from typing import List, Union, Dict, Callable, Set

import sinter
import stim

import gen


def make_bacon_shor_patch(width: int, height: int) -> gen.StabilizerCode:
    tiles = []
    for x in range(width):
        for y in range(height):
            c = x + y*1j
            if x < width - 1:
                tiles.append(gen.Tile(
                    ordered_data_qubits=[c, c + 1],
                    measurement_qubit=c + 0.5,
                    bases='X',
                ))
            if y < height - 1:
                tiles.append(gen.Tile(
                    ordered_data_qubits=[c, c + 1j],
                    measurement_qubit=c + 0.5j,
                    bases='Z',
                ))

    patch = gen.Patch(tiles)
    xs = gen.PauliString({q: 'X' for q in patch.data_set if q.real == 0})
    zs = gen.PauliString({q: 'Z' for q in patch.data_set if q.imag == 0})
    return gen.StabilizerCode(patch=patch, obs_x=xs, obs_z=zs)


def make_bacon_shor_round(
        *,
        width: int,
        height: int,
        basis: str,
        init: bool,
        end: bool,
) -> gen.Chunk:
    code = make_bacon_shor_patch(width=width, height=height)
    patch = code.patch
    patch_x = gen.Patch(tile for tile in patch.tiles if tile.basis == 'X')
    patch_z = gen.Patch(tile for tile in patch.tiles if tile.basis == 'Z')

    builder = gen.Builder.for_qubits(patch.data_set)

    if init:
        builder.gate(f'R{basis}', patch.data_set)
        builder.tick()

    for xx in patch_x.tiles:
        if xx.measurement_qubit.real % 2 == 0.5:
            builder.measure_pauli_product(xs=xx.data_set, key=gen.AtLayer(xx.measurement_qubit, 'solo'))
    builder.tick()
    for xx in patch_x.tiles:
        if xx.measurement_qubit.real % 2 == 1.5:
            builder.measure_pauli_product(xs=xx.data_set, key=gen.AtLayer(xx.measurement_qubit, 'solo'))
    builder.tick()
    for zz in patch_z.tiles:
        if zz.measurement_qubit.imag % 2 == 0.5:
            builder.measure_pauli_product(zs=zz.data_set, key=gen.AtLayer(zz.measurement_qubit, 'solo'))
    builder.tick()
    for zz in patch_z.tiles:
        if zz.measurement_qubit.imag % 2 == 1.5:
            builder.measure_pauli_product(zs=zz.data_set, key=gen.AtLayer(zz.measurement_qubit, 'solo'))

    if end:
        builder.tick()
        builder.measure(patch.data_set, basis=basis, save_layer='end')

    groups = {
        **sinter.group_by(patch_x.tiles, key=lambda e: e.measurement_qubit.real),
        **sinter.group_by(patch_z.tiles, key=lambda e: 1j*e.measurement_qubit.imag),
    }
    flows = []
    if init:
        for tile in patch.tiles:
            if tile.basis == basis == 'X':
                flows.append(gen.Flow(
                    measurement_indices=builder.tracker.measurement_indices([gen.AtLayer(tile.measurement_qubit, 'solo')]),
                    center=tile.measurement_qubit,
                ))
    if end:
        for tile in patch.tiles:
            if tile.basis == basis == 'Z':
                flows.append(gen.Flow(
                    measurement_indices=builder.tracker.measurement_indices([
                        gen.AtLayer(tile.measurement_qubit, 'solo'),
                    ] + [
                        gen.AtLayer(q, 'end')
                        for q in tile.data_set
                    ]),
                    center=tile.measurement_qubit,
                ))
    for key, group in groups.items():
        ps = gen.PauliString({})
        ms = []
        for tile in group:
            ps *= gen.PauliString.from_tile_data(tile)
            ms.append(gen.AtLayer(tile.measurement_qubit, 'solo'))
        tm = builder.tracker.measurement_indices(ms)
        tile_basis, = set(ps.qubits.values())
        if not init or tile_basis == basis == 'Z':
            flows.append(gen.Flow(
                start=None if init else ps,
                measurement_indices=tm,
                center=key,
            ))
        if not end or tile_basis == basis == 'X':
            flows.append(gen.Flow(
                end=None if end else ps,
                measurement_indices=tm if not end else builder.tracker.measurement_indices(ms + [
                    gen.AtLayer(q, 'end') for q in ps.qubits.keys()
                ]),
                center=key,
            ))

    if basis == 'X':
        flows.append(gen.Flow(
            start=None if init else code.obs_x,
            end=None if end else code.obs_x,
            measurement_indices=builder.tracker.measurement_indices([
                gen.AtLayer(q, 'end')
                for q in code.obs_x.qubits.keys()
            ] if end else []),
            center=0,
            obs_index=0,
        ))
    elif basis == 'Z':
        flows.append(gen.Flow(
            start=None if init else code.obs_z,
            end=None if end else code.obs_z,
            measurement_indices=builder.tracker.measurement_indices([
                gen.AtLayer(q, 'end')
                for q in code.obs_z.qubits.keys()
            ] if end else []),
            center=0,
            obs_index=0,
        ))
    else:
        raise NotImplementedError(f'{basis=}')

    return gen.Chunk(
        circuit=builder.circuit,
        q2i=builder.q2i,
        flows=flows,
    )


def make_bacon_shor_circuit(
        *,
        width: int,
        height: int,
        basis: str,
        rounds: int,
) -> List[gen.Chunk]:
    assert rounds > 0
    if rounds == 1:
        return [
            make_bacon_shor_round(
                width=width,
                height=height,
                basis=basis,
                init=True,
                end=True,
            )
        ]
    init = make_bacon_shor_round(
        width=width,
        height=height,
        basis=basis,
        init=True,
        end=False,
    )
    bulk = make_bacon_shor_round(
        width=width,
        height=height,
        basis=basis,
        init=False,
        end=False,
    )
    end = make_bacon_shor_round(
        width=width,
        height=height,
        basis=basis,
        init=False,
        end=True,
    )
    return [
        init,
        gen.ChunkLoop([bulk], rounds - 2),
        end
    ]


def _bacon_shor_circuit_chunks_from_params(params: gen.CircuitBuildParams) -> List[Union[gen.Chunk, gen.ChunkLoop]]:
    return make_bacon_shor_circuit(
        width=params.diameter,
        height=params.diameter,
        basis=params.custom['b'],
        rounds=params.rounds,
    )


def make_bacon_shor_constructions() -> Dict[str, Callable[[gen.CircuitBuildParams], List[Union[gen.Chunk, gen.ChunkLoop]]]]:
    return {
        'bacon_shor': _bacon_shor_circuit_chunks_from_params,
    }
