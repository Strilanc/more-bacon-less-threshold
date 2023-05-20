import argparse
import dataclasses
import itertools
import pathlib
from typing import Union, List, Optional, Dict, \
    Callable, Any

import stim

from gen._chunk import Chunk, ChunkLoop
from gen._flow_util import compile_chunks_into_circuit
from gen._layer_translate import to_z_basis_interaction_circuit
from gen._noise import NoiseModel
from gen._patch import Patch
from gen._util import write_file
from gen._viz_circuit_html import stim_circuit_html_viewer
from gen._viz_patch_svg import patch_svg_viewer


@dataclasses.dataclass
class CircuitBuildParams:
    style: str
    rounds: int
    diameter: int
    custom: Dict[str, Any]


def main_generate_circuits(
        *,
        constructions: Dict[str, Callable[[CircuitBuildParams], List[Chunk]]],
        extras: Optional[Dict[str, type]] = None,
) -> None:
    if extras is None:
        extras = {}
    parser = argparse.ArgumentParser()
    parser.add_argument("--out_dir", type=str, required=True)
    parser.add_argument("--diameter", nargs='+', required=True, type=int)
    parser.add_argument("--rounds", nargs='+', required=True, type=str)
    parser.add_argument("--noise_strength", nargs='+', default=(None,), type=float)
    parser.add_argument("--noise_model", nargs='+', required=True, choices=['si1000', 'uniform', 'None'])
    parser.add_argument("--style", nargs='+', required=True, choices=constructions.keys())
    parser.add_argument("--convert_to_cz", nargs='+', default=('auto',), choices=['auto', '1', '0'])
    parser.add_argument("--debug_out_dir", default=None, type=str)
    parser.add_argument("--custom", default=None)
    for extra in extras:
        parser.add_argument("--" + extra, nargs='+', type=extras[extra], default=None)
    args = parser.parse_args()

    _generate_circuits(
        constructions=constructions,
        diameters=args.diameter,
        noise_strengths=args.noise_strength,
        rounds_funcs=args.rounds,
        noise_model_names=args.noise_model,
        styles=args.style,
        extras={extra: getattr(args, extra) for extra in extras},
        customs=args.custom,
        convert_to_czs=args.convert_to_cz,
        debug_out_dir=args.debug_out_dir,
        out_dir=args.out_dir,
    )


def _generate_circuits(
        *,
        constructions: Dict[str, Callable[[CircuitBuildParams], List['Chunk']]],
        diameters: List[int],
        noise_strengths: List[float],
        rounds_funcs: List[str],
        noise_model_names: List[str],
        styles: List[str],
        extras: Dict[str, Optional[List[Any]]],
        customs: Optional[str],
        convert_to_czs: List[str],
        debug_out_dir: Union[None, str, pathlib.Path],
        out_dir: Union[str, pathlib.Path],
) -> None:
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(exist_ok=True, parents=True)
    if debug_out_dir is not None:
        debug_out_dir = pathlib.Path(debug_out_dir)
        debug_out_dir.mkdir(exist_ok=True, parents=True)

    extras_product = itertools.product(*[
        [(k, v) for v in vs]
        for k, vs in extras.items()
        if vs is not None
    ])
    for (
        diameter,
        noise_strength,
        rounds_func,
        noise_model_name,
        style,
        item_extras,
        convert_to_cz_arg,
    ) in itertools.product(
        diameters,
        noise_strengths,
        rounds_funcs,
        noise_model_names,
        styles,
        extras_product,
        convert_to_czs,
    ):
        if noise_model_name != "None" and noise_strength is None:
            raise ValueError("Must specify --noise_strength")
        auto_cz = False
        if noise_model_name in ['SI1000', 'si1000']:
            noise_model = NoiseModel.si1000(noise_strength)
            auto_cz = True
        elif noise_model_name in ['uniform', 'UniformDepolarizing']:
            noise_model = NoiseModel.uniform_depolarizing(noise_strength)
        elif noise_model_name == "None":
            noise_model = None
        else:
            raise NotImplementedError(f'{noise_model_name=}')

        rounds = eval(rounds_func, {'d': diameter})
        if convert_to_cz_arg == 'auto':
            convert_to_cz = auto_cz
        else:
            convert_to_cz = bool(int(convert_to_cz_arg))
        extras_dict = {k: v for k, v in item_extras}
        if customs is not None:
            custom_dict = eval(customs, {'d': diameter}, {})
            assert isinstance(custom_dict, dict)
        else:
            custom_dict = {}
        assert custom_dict.keys().isdisjoint(extras_dict.keys())
        circuit = _generate_single_circuit(
            constructions=constructions,
            params=CircuitBuildParams(style=style, rounds=rounds, diameter=diameter, custom={**extras_dict, **custom_dict}),
            noise=noise_model,
            debug_out_dir=debug_out_dir,
            convert_to_cz=convert_to_cz,
        )
        q = circuit.num_qubits
        extra_tags = ''
        for k, v in item_extras:
            extra_tags += f',{k}={v}'
        if convert_to_cz:
            extra_tags += ',g=cz'
        else:
            extra_tags += ',g=all'
        for k, v in custom_dict.items():
            extra_tags += f',{k}={v}'
        path = out_dir / f'r={rounds},d={diameter},p={noise_strength},noise={noise_model_name},c={style},q={q}{extra_tags}.stim'
        with open(path, 'w') as f:
            print(circuit, file=f)
        print(f'wrote file://{path.absolute()}')


def _generate_single_circuit(
        *,
        constructions: Dict[str, Callable[[CircuitBuildParams], List['Chunk']]],
        noise: Optional[NoiseModel],
        params: CircuitBuildParams,
        debug_out_dir: Union[None, str, pathlib.Path] = None,
        convert_to_cz: bool = True,
) -> stim.Circuit:
    if debug_out_dir is not None:
        debug_out_dir = pathlib.Path(debug_out_dir)
        debug_out_dir.mkdir(exist_ok=True, parents=True)

    construction = constructions.get(params.style)
    if construction is None:
        raise NotImplementedError(f'{params=}')
    chunks = construction(params)

    return generate_noisy_circuit_from_chunks(
        chunks=chunks,
        allow_magic_chunks='magic' in params.style,
        noise=noise,
        debug_out_dir=debug_out_dir,
        convert_to_cz=convert_to_cz,
    )


def generate_noisy_circuit_from_chunks(
        *,
        chunks: List[Union[Chunk, ChunkLoop]],
        noise: Optional[NoiseModel],
        allow_magic_chunks: bool,
        convert_to_cz: bool,
        debug_out_dir: Union[None, str, pathlib.Path] = None,
) -> stim.Circuit:
    if debug_out_dir is not None:
        debug_out_dir = pathlib.Path(debug_out_dir)
        debug_out_dir.mkdir(exist_ok=True, parents=True)

    if not allow_magic_chunks:
        assert all(not chunk.magic for chunk in chunks)

    if debug_out_dir is not None:
        patches = [chunk.end_patch() for chunk in chunks[:-1]]
        changed_patches = [patches[k] for k in range(len(patches)) if k == 0 or patches[k] != patches[k-1]]
        allowed_qubits = {q for patch in changed_patches for q in patch.used_set}
        write_file(debug_out_dir / "patch.svg", patch_svg_viewer(
            changed_patches,
            show_order=False,
            available_qubits=allowed_qubits,
        ))

    if debug_out_dir is not None:
        ignore_errors_ideal_circuit = compile_chunks_into_circuit(chunks, ignore_errors=True)
        patch_dict = {}
        cur_tick = 0
        last_patch = Patch([])
        if chunks[0].start_patch() != last_patch:
            patch_dict[0] = chunks[0].start_patch()
            last_patch = chunks[0].start_patch()
            cur_tick += 1

        for c in ChunkLoop(chunks, repetitions=1).flattened():
            cur_tick += c.tick_count()
            if c.end_patch() != last_patch:
                patch_dict[cur_tick] = c.end_patch().without_wraparound_tiles()
                last_patch = c.end_patch()
                cur_tick += 1
        write_file(debug_out_dir / "ideal_circuit.html", stim_circuit_html_viewer(
            ignore_errors_ideal_circuit,
            patch=patch_dict,
        ))
        write_file(debug_out_dir / "ideal_circuit.stim", ignore_errors_ideal_circuit)
        write_file(debug_out_dir / "ideal_circuit_dets.svg", ignore_errors_ideal_circuit.diagram("time+detector-slice-svg"))

    body = compile_chunks_into_circuit(chunks).with_inlined_feedback()
    mpp_indices = [
        k
        for k, inst in enumerate(body)
        if isinstance(inst, stim.CircuitInstruction) and inst.name == 'MPP'
    ]
    skip_mpp_head = chunks[0].magic
    skip_mpp_tail = chunks[-1].magic
    body_start = mpp_indices[0] + 2 if skip_mpp_head else 0
    body_end = mpp_indices[-1] if skip_mpp_tail else len(body)
    magic_head = body[:body_start]
    magic_tail = body[body_end:]
    body = body[body_start:body_end]

    if convert_to_cz:
        body = to_z_basis_interaction_circuit(body, is_entire_circuit=len(magic_head) == len(magic_tail) == 0)
        if debug_out_dir is not None:
            ideal_circuit = magic_head + body + magic_tail
            write_file(debug_out_dir / "ideal_cz_circuit.html", stim_circuit_html_viewer(
                ideal_circuit,
                patch=chunks[0].end_patch().without_wraparound_tiles(),
            ))
            write_file(debug_out_dir / "ideal_cz_circuit.stim", ideal_circuit)
            write_file(debug_out_dir / "ideal_cz_circuit_dets.svg", ideal_circuit.diagram("time+detector-slice-svg"))

    if noise is not None:
        body = noise.noisy_circuit(body)
    noisy_circuit = magic_head + body + magic_tail

    if debug_out_dir is not None:
        write_file(debug_out_dir / "noisy_circuit.html", stim_circuit_html_viewer(
            noisy_circuit,
            patch=chunks[0].end_patch().without_wraparound_tiles(),
        ))
        write_file(debug_out_dir / "noisy_circuit.stim", noisy_circuit)
        write_file(debug_out_dir / "noisy_circuit_dets.svg", noisy_circuit.diagram("time+detector-slice-svg"))

    return noisy_circuit
