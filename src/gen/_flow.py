from typing import Iterable, Tuple, Any, Optional, Dict, Callable

import stim

import gen
from gen._tile import Tile
from gen._util import sorted_complex


class PauliString:
    """A qubit-to-pauli mapping."""
    def __init__(self, qubits: Dict[complex, str]):
        self.qubits = {q: qubits[q] for q in gen.sorted_complex(qubits.keys())}
        self._hash = hash(tuple(self.qubits.items()))

    @staticmethod
    def from_stim_pauli_string(stim_pauli_string: stim.PauliString) -> 'PauliString':
        return PauliString({
            q: '_XYZ'[stim_pauli_string[q]]
            for q in range(len(stim_pauli_string))
            if stim_pauli_string[q]
        })

    def __bool__(self):
        return bool(self.qubits)

    def __mul__(self, other: 'PauliString') -> 'PauliString':
        result = {}
        for q in self.qubits.keys() | other.qubits.keys():
            a = self.qubits.get(q, 'I')
            b = other.qubits.get(q, 'I')
            ax = a in 'XY'
            az = a in 'YZ'
            bx = b in 'XY'
            bz = b in 'YZ'
            cx = ax ^ bx
            cz = az ^ bz
            c = 'IXZY'[cx + cz*2]
            if c != 'I':
                result[q] = c
        return PauliString(result)

    def __repr__(self):
        return f'PauliString(qubits={self.qubits!r})'

    def __str__(self):
        return '*'.join(
            f'{self.qubits[q]}{q}'
            for q in sorted_complex(self.qubits.keys())
        )


    def with_xz_flipped(self) -> 'PauliString':
        return PauliString({
            q: "Z" if p == 'X' else 'X' if p == 'Z' else p for q, p in self.qubits.items()
        })

    def anticommutes(self, other: 'PauliString') -> bool:
        t = 0
        for q in self.qubits.keys() & other.qubits.keys():
            t += self.qubits[q] != other.qubits[q]
        return t % 2 == 1

    def with_transformed_coords(self, transform: Callable[[complex], complex]) -> 'PauliString':
        return PauliString({
            transform(q): p for q, p in self.qubits.items()
        })

    @staticmethod
    def from_tile_data(tile: Tile) -> 'PauliString':
        return PauliString({
            k: v
            for k, v in zip(tile.ordered_data_qubits, tile.bases)
            if k is not None
        })

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        if not isinstance(other, PauliString):
            return NotImplemented
        return self.qubits == other.qubits


class Flow:
    """A rule for how a stabilizer travels into, through, and/or out of a chunk.
    """

    def __init__(self,
                 *,
                 start: Optional[PauliString] = None,
                 end: Optional[PauliString] = None,
                 measurement_indices: Iterable[int] = (),
                 obs_index: Any = None,
                 additional_coords: Iterable[float] = (),
                 center: complex,
                 postselect: bool = False,
                 allow_vacuous: bool = False,
                 ):
        if not allow_vacuous:
            assert start or end or measurement_indices, "vacuous flow"
        self.start = PauliString({}) if start is None else start
        self.end = PauliString({}) if end is None else end
        self.measurement_indices: Tuple[int, ...] = tuple(measurement_indices)
        self.additional_coords = tuple(additional_coords)
        self.obs_index = obs_index
        self.center = center
        self.postselect = postselect

    def __eq__(self, other):
        if not isinstance(other, Flow):
            return NotImplemented
        return (self.start == other.start and
                self.end == other.end and
                self.measurement_indices == other.measurement_indices and
                self.obs_index == other.obs_index and
                self.additional_coords == other.additional_coords and
                self.center == other.center and
                self.postselect == other.postselect)

    def __repr__(self):
        return (f'Flow(start={self.start!r}, '
                f'end={self.end!r}, '
                f'measurement_indices={self.measurement_indices!r}, '
                f'additional_coords={self.additional_coords!r}, '
                f'obs_index={self.obs_index!r}, '
                f'postselect={self.postselect!r})')

    def postselected(self) -> 'Flow':
        return Flow(
            start=self.start,
            end=self.end,
            measurement_indices=self.measurement_indices,
            obs_index=self.obs_index,
            additional_coords=self.additional_coords,
            center=self.center,
            postselect=True,
        )

    def with_xz_flipped(self) -> 'Flow':
        return Flow(
            start=self.start.with_xz_flipped(),
            end=self.end.with_xz_flipped(),
            measurement_indices=self.measurement_indices,
            obs_index=self.obs_index,
            additional_coords=self.additional_coords,
            center=self.center,
            postselect=self.postselect,
        )

    def with_transformed_coords(self, transform: Callable[[complex], complex]) -> 'Flow':
        return Flow(
            start=self.start.with_transformed_coords(transform),
            end=self.end.with_transformed_coords(transform),
            measurement_indices=self.measurement_indices,
            obs_index=self.obs_index,
            additional_coords=self.additional_coords,
            center=transform(self.center),
            postselect=self.postselect,
        )

    def concat(self, other: 'Flow', other_measure_offset: int) -> 'Flow':
        if other.start != self.end:
            raise ValueError('other.start != self.end')
        if other.obs_index != self.obs_index:
            raise ValueError('other.obs_index != self.obs_index')
        if other.additional_coords != self.additional_coords:
            raise ValueError('other.additional_coords != self.additional_coords')
        return Flow(
            start=self.start,
            end=other.end,
            center=(self.center + other.center) / 2,
            measurement_indices=self.measurement_indices + tuple(m + other_measure_offset for m in other.measurement_indices),
            obs_index=self.obs_index,
            additional_coords=self.additional_coords,
            postselect=self.postselect or other.postselect,
        )
