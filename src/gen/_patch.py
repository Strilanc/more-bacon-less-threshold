import functools
import pathlib
from typing import Tuple, Iterable, FrozenSet, Callable, Union, Literal, \
    Optional, Any, Dict, List, AbstractSet

from gen._builder import Builder, AtLayer
from gen._interaction_planner import DESIRED_Z_TO_ORIENTATION
from gen._tile import Tile
from gen._util import sorted_complex, write_file


class Patch:
    """A collection of annotated stabilizers to measure simultaneously.
    """

    def __init__(self,
                 tiles: Iterable[Tile],
                 *,
                 data_idle_orientations: Optional[Dict[complex, str]] = None,
                 do_not_sort: bool = False):
        self.data_idle_orientations = data_idle_orientations or {}
        if do_not_sort:
            self.tiles = tuple(tiles)
        else:
            self.tiles = tuple(sorted_complex(tiles, key=lambda e: e.measurement_qubit))

    def after_coordinate_transform(self, coord_transform: Callable[[complex], complex]) -> 'Patch':
        return Patch(
            [e.after_coordinate_transform(coord_transform) for e in self.tiles],
            data_idle_orientations={coord_transform(q): p for q, p in self.data_idle_orientations}
        )

    def after_basis_transform(self, basis_transform: Callable[[str], str]) -> 'Patch':
        return Patch(
            [e.after_basis_transform(basis_transform) for e in self.tiles],
            data_idle_orientations={q: basis_transform(p) for q, p in self.data_idle_orientations}
        )

    def without_wraparound_tiles(self) -> 'Patch':
        p0, p1 = _bounds(self.data_set)
        def keep_tile(tile: Tile) -> bool:
            t0, t1 = _bounds(tile.data_set)
            if t0.real == p0.real and t1.real == p1.real:
                return False
            if t0.imag == p0.imag and t1.imag == p1.imag:
                return False
            return True
        return Patch([t for t in self.tiles if keep_tile(t)], data_idle_orientations=self.data_idle_orientations)

    @functools.cached_property
    def m2p(self) -> Dict[complex, Tile]:
        return {e.measurement_qubit: e for e in self.tiles}

    def with_opposite_order(self) -> 'Patch':
        return Patch(tiles=[
            Tile(
                bases=tile.bases[::-1],
                measurement_qubit=tile.measurement_qubit,
                ordered_data_qubits=tile.ordered_data_qubits[::-1],
            )
            for tile in self.tiles
        ], data_idle_orientations=self.data_idle_orientations)

    def with_contracted_measurements(self, f: float = 0.2) -> 'Patch':
        tiles = []
        for tile in self.tiles:
            m = tile.measurement_qubit * (1 - f) + sum(tile.ordered_data_qubits) / len(tile.ordered_data_qubits) * f
            tiles.append(Tile(
                ordered_data_qubits=tile.ordered_data_qubits,
                measurement_qubit=m,
                bases=tile.bases,
            ))
        return Patch(tiles, data_idle_orientations=self.data_idle_orientations)

    def write_svg(
            self,
            path: Union[str, pathlib.Path],
            *,
            other: Union['Patch', Iterable['Patch']] = (),
            show_order: Union[bool, Literal['undirected', '3couplerspecial']] = True,
            show_measure_qubits: bool = True,
            show_data_qubits: bool = False,
            system_qubits: Iterable[complex] = (),
            opacity: float = 1,
    ) -> None:
        from gen._viz_patch_svg import patch_svg_viewer
        viewer = patch_svg_viewer(
            patches=[self] + ([other] if isinstance(other, Patch) else list(other)),
            show_measure_qubits=show_measure_qubits,
            show_data_qubits=show_data_qubits,
            show_order=show_order,
            available_qubits=system_qubits,
            opacity=opacity,
        )
        write_file(path, viewer)

    def with_xz_flipped(self) -> 'Patch':
        trans = {'X': 'Z', 'Y': 'Y', 'Z': 'X'}
        return self.after_basis_transform(trans.__getitem__)

    @functools.cached_property
    def used_set(self) -> FrozenSet[complex]:
        result = set()
        for e in self.tiles:
            result |= e.used_set
        return frozenset(result)

    @functools.cached_property
    def data_set(self) -> FrozenSet[complex]:
        result = set()
        for e in self.tiles:
            for q in e.ordered_data_qubits:
                if q is not None:
                    result.add(q)
        return frozenset(result)

    def __eq__(self, other):
        if not isinstance(other, Patch):
            return NotImplemented
        return self.tiles == other.tiles

    def __ne__(self, other):
        return not (self == other)

    @functools.cached_property
    def measure_set(self) -> FrozenSet[complex]:
        return frozenset(e.measurement_qubit for e in self.tiles)

    def bounding_box(self, extras: Iterable[complex] = ()) -> Tuple[complex, complex]:
        qs = self.used_set | set(extras)
        min_r = min((e.real for e in qs), default=0)
        min_i = min((e.imag for e in qs), default=0)
        max_r = max((e.real for e in qs), default=0)
        max_i = max((e.imag for e in qs), default=0)
        return min_r + min_i * 1j, max_r + max_i * 1j

    def __repr__(self):
        return '\n'.join([
            'gen.Patch(tiles=[',
            *[f'    {e!r},'.replace('\n', '\n    ') for e in self.tiles],
            '])',
        ])

    def _measure_cz(self,
                    *,
                    data_resets: Dict[complex, str],
                    data_measures: Dict[complex, str],
                    builder: Builder,
                    tracker_key: Callable[[complex], Any],
                    tracker_layer: float) -> None:
        assert self.measure_set.isdisjoint(data_resets)
        if not self.tiles:
            return

        builder.gate('R', data_resets.keys() | self.measure_set)
        builder.tick()

        num_layers, = {len(e.ordered_data_qubits) for e in self.tiles}
        start_orientations = {
            **self.data_idle_orientations,
            **{q: DESIRED_Z_TO_ORIENTATION[b] for q, b in data_resets.items()},
        }
        end_orientations = {
            **self.data_idle_orientations,
            **{q: DESIRED_Z_TO_ORIENTATION[b] for q, b in data_measures.items()},
        }
        with builder.plan_interactions(
                layer_count=num_layers,
                start_orientations=start_orientations,
                end_orientations=end_orientations,
        ) as planner:
            for k in range(num_layers):
                for e in self.tiles:
                    q = e.ordered_data_qubits[k]
                    if q is not None:
                        planner.pcp(e.bases[k], 'X', q, e.measurement_qubit, layer=k)

        builder.tick()
        builder.measure(data_measures.keys() | self.measure_set,
                        tracker_key=tracker_key,
                        save_layer=tracker_layer)

    def _measure_mpp(self,
                     *,
                     data_resets: Dict[complex, str],
                     data_measures: Dict[complex, str],
                     builder: Builder,
                     tracker_key: Callable[[complex], Any],
                     tracker_layer: float) -> None:
        assert self.measure_set.isdisjoint(data_resets)

        if data_resets:
            for b in 'XYZ':
                builder.gate(f'R{b}', {q for q, db in data_resets.items() if b == db})

        for v in self.tiles:
            builder.measure_pauli_product(
                q2b={q: b for q, b in zip(v.ordered_data_qubits, v.bases) if q is not None},
                key=AtLayer(tracker_key(v.measurement_qubit), tracker_layer)
            )

        if data_measures:
            for b in 'XYZ':
                builder.measure({q for q, db in data_measures.items() if b == db},
                                basis=b,
                                tracker_key=tracker_key,
                                save_layer=tracker_layer)

    def measure(self,
                *,
                data_resets: Optional[Dict[complex, str]] = None,
                data_measures: Optional[Dict[complex, str]] = None,
                builder: Builder,
                tracker_key: Callable[[complex], Any] = lambda e: e,
                save_layer: Any,
                style: str = 'cz') -> None:
        if data_resets is None:
            data_resets = {}
        if data_measures is None:
            data_measures = {}
        if style == 'cz':
            self._measure_cz(
                data_resets=data_resets,
                data_measures=data_measures,
                builder=builder,
                tracker_key=tracker_key,
                tracker_layer=save_layer,
            )
        elif style == 'mpp':
            self._measure_mpp(
                data_resets=data_resets,
                data_measures=data_measures,
                builder=builder,
                tracker_key=tracker_key,
                tracker_layer=save_layer,
            )
        else:
            raise NotImplementedError(f'{style=}')

    def detect(self,
               *,
               comparison_overrides: Optional[Dict[Any, Optional[List[Any]]]] = None,
               skipped_comparisons: Iterable[Any] = (),
               singleton_detectors: Iterable[Any] = (),
               data_resets: Optional[Dict[complex, str]] = None,
               data_measures: Optional[Dict[complex, str]] = None,
               builder: Builder,
               repetitions: Optional[int] = None,
               tracker_key: Callable[[complex], Any] = lambda e: e,
               tracker_layer: int,
               tracker_layer_last_rep: Optional[int] = None,
               prev_tracker_layer: Optional[int] = None,
               post_selected_positions: AbstractSet[complex] = frozenset(),
               style: str = 'cz') -> None:
        if prev_tracker_layer is None:
            prev_tracker_layer = tracker_layer - 1
        if data_resets is None:
            data_resets = {}
        if data_measures is None:
            data_measures = {}
        assert (repetitions is not None) == (tracker_layer_last_rep is not None)
        if repetitions is not None:
            assert not data_resets
            assert not data_measures
        if repetitions == 0:
            for plaq in self.tiles:
                m = plaq.measurement_qubit
                builder.tracker.make_measurement_group([AtLayer(m, prev_tracker_layer)], key=AtLayer(m, tracker_layer_last_rep))
            return

        child = builder.fork()
        pm = builder.tracker.next_measurement_index
        self.measure(
            data_resets=data_resets,
            data_measures=data_measures,
            builder=child,
            tracker_key=tracker_key,
            save_layer=tracker_layer,
            style=style,
        )
        num_measurements = builder.tracker.next_measurement_index - pm

        if comparison_overrides is None:
            comparison_overrides = {}
        assert self.measure_set.isdisjoint(data_resets)
        skipped_comparisons_set = frozenset(skipped_comparisons)
        singleton_detectors_set = frozenset(singleton_detectors)
        for e in sorted_complex(self.tiles, key=lambda e2: e2.measurement_qubit):
            if all(e is None for e in e.ordered_data_qubits):
                continue
            m = e.measurement_qubit
            if m in skipped_comparisons_set:
                continue
            if m in singleton_detectors_set:
                comparisons = []
            else:
                comparisons = comparison_overrides.get(m, [AtLayer(m, prev_tracker_layer)])
            if comparisons is None:
                continue
            assert isinstance(comparisons,
                              list), f"Vs exception must be a list but got {comparisons!r} for {m!r}"
            child.detector([AtLayer(m, tracker_layer), *comparisons], pos=m, mark_as_post_selected=m in post_selected_positions)
        child.circuit.append("SHIFT_COORDS", [], [0, 0, 1])
        specified_reps = repetitions is not None
        if repetitions is None:
            repetitions = 1
        if specified_reps:
            child.tick()

        if repetitions > 1 or tracker_layer_last_rep is not None:
            if tracker_layer_last_rep is None:
                raise ValueError("repetitions > 1 and tracker_layer_last_rep is None")
            offset = num_measurements * (repetitions - 1)
            builder.tracker.next_measurement_index += offset
            for m in data_measures.keys() | self.measure_set:
                builder.tracker.recorded[AtLayer(m, tracker_layer_last_rep)] = [e + offset for e in builder.tracker.recorded[AtLayer(m, tracker_layer)]]
        builder.circuit += child.circuit * repetitions

    def with_reverse_order(self) -> 'Patch':
        return Patch(
            tiles=[
                Tile(
                    bases=plaq.bases[::-1],
                    measurement_qubit=plaq.measurement_qubit,
                    ordered_data_qubits=plaq.ordered_data_qubits[::-1],
                )
                for plaq in self.tiles
            ],
            data_idle_orientations=self.data_idle_orientations,
        )


def _bounds(qubits: Iterable[complex]) -> Tuple[complex, complex]:
    min_r = min([q.real for q in qubits], default=0)
    min_i = min([q.imag for q in qubits], default=0)
    max_r = max([q.real for q in qubits], default=0)
    max_i = max([q.imag for q in qubits], default=0)
    return min_r + min_i*1j, max_r + max_i*1j
