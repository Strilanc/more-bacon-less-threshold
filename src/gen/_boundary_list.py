import collections
from typing import Iterable, List, Set, Dict, Tuple, Optional, Callable

from gen._tile import Tile
from gen._patch import Patch
from gen._util import sorted_complex

UL, UR, DL, DR = [e * 0.5 for e in [-1 - 1j, +1 - 1j, -1 + 1j, +1 + 1j]]
Order_Z = [UL, UR, DL, DR]
Order_ᴎ = [UL, DL, UR, DR]
Order_N = [DL, UL, DR, UR]
Order_S = [DL, DR, UL, UR]


def checkerboard_basis(q: complex) -> str:
    """Classifies a coordinate as X type or Z type according to a checkerboard.
    """
    is_x = int(q.real + q.imag) & 1 == 0
    return 'X' if is_x else 'Z'


class Curve:
    """A closed series of line segments between integer coordinates aligned at 45 degree angles.

    Each line segment has an associated basis (X or Z).
    """
    def __init__(self, *, points: Iterable[complex] = (), bases: Iterable[str] = ()):
        self.points = list(points)
        self.bases = list(bases)

    def copy(self) -> 'Curve':
        return Curve(points=self.points, bases=self.bases)

    def line_to(self, basis: str, target: complex) -> None:
        """Adds a line segment to the curve.

        If this isn't the first segment, the previous endpoint is the end of the previous segment.
        If this is the first segment, the previous endpoint is the end of the (eventual) last segment.

        Args:
            basis: The type of line segment (X or Z).
            target: The endpoint of the line segment.
        """
        self.bases.append(basis)
        self.points.append(target)

    def min_max(self) -> Tuple[complex, complex]:
        """Returns an axis-aligned bounding box  for the curve.

        Returns:
            A (minimum_real_imag, maximum_real_imag) tuple.
        """
        min_r = min(q.real for q in self.points)
        min_i = min(q.imag for q in self.points)
        max_r = max(q.real for q in self.points)
        max_i = max(q.imag for q in self.points)
        return min_r + min_i*1j, max_r + max_i*1j

    def med(self) -> complex:
        """Returns the center of the axis-aligned bounding box of the curve."""
        a, b = self.min_max()
        return (a.real + b.real) // 2 + (a.imag + b.imag) // 2 * 1j

    def __len__(self):
        """Returns the number of line segments making up the curve."""
        return len(self.points)

    def __getitem__(self, item: int) -> Tuple[str, complex, complex]:
        assert isinstance(item, int)
        return self.bases[item], self.points[item - 1], self.points[item]

    def segment_indices_intersecting(self, points: Set[complex]) -> List[int]:
        """Returns the indiceds of line segments intersecting the given point set."""
        hits = []
        for k in range(len(self.points)):
            a = self.points[k - 1]
            b = self.points[k]
            if any(e in points for e in int_points_on_line(a, b)):
                hits.append(k)
        return hits

    def offset_by(self, offset: complex) -> 'Curve':
        """Translates the curve's location by translating all of its line segments."""
        return Curve(points=[p + offset for p in self.points], bases=self.bases)

    def boundary_set(self) -> Set[complex]:
        """Returns the set of integer coordinates along the line segments of the curve."""
        return set(int_travel_points_on_polygon_boundary(self.points))

    def boundary_travel(self) -> List[complex]:
        """Lists the integer coordinates along the line segments of the curve, in order."""
        return int_travel_points_on_polygon_boundary(self.points)

    def __eq__(self, other):
        if not isinstance(other, Curve):
            return NotImplemented
        return self.points == other.points and self.bases == other.bases

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return f'Curve(points={self.points!r}, bases={"".join(self.bases)!r})'


class BoundaryList:
    """Defines a surface code stabilizer configuration in terms of its boundaries.
    """

    def __init__(self, curves: Iterable[Curve]):
        """
        Args:
            curves: The curves defining the boundaries of the patch.
                These curves should not intersect each other, but may be inside each other, creating
                interior voids or nested islands.
        """
        self.curves = list(curves)

    def boundary(self) -> Set[complex]:
        """Returns the set of integer coordinates that are on any of the boundary curves."""
        result = set()
        for c in self.curves:
            result |= c.boundary_set()
        return result

    def interior(self, *, include_boundary: bool) -> Set[complex]:
        """Returns the set of integer coordinates that are inside the bounded area.

        Args:
            include_boundary: Whether or not boundary points are considered part of the
                interior or not.
        """
        return int_points_inside_polygon_set([
            c.points for c in self.curves
        ], include_boundary=include_boundary)

    def disjoint_interiors(self, *, include_boundary: bool) -> Dict[int, Set[complex]]:
        """Groups the interior by connected component.

        Args:
            include_boundary: Whether or not boundary points are considered part of the
                interior or not.

        Returns:
            A (mask -> interior) dictionary where the mask is the set of curves the interior is
            within and the interior is a set of integer coordinates.
        """
        return int_point_disjoint_regions_inside_polygon_set([
            c.points for c in self.curves
        ], include_boundary=include_boundary)

    def copy(self) -> 'BoundaryList':
        return BoundaryList([e.copy() for e in self.curves])

    def fused(self, a: complex, b: complex) -> 'BoundaryList':
        """Performs lattice surgery between the two segments intersected by the line from a to b.

        It is assumed that there are exactly two segments along the line from a to b.
        It is assumed that these two segments' endpoints are equal when perp-projecting
        onto the a-to-b vector.

        Returns:
            A boundary list containing the stitched result.
        """
        hits = []
        pts = set(int_points_on_line(a, b))
        for k in range(len(self.curves)):
            for e in self.curves[k].segment_indices_intersecting(pts):
                hits.append((k, e))
        if len(hits) != 2:
            raise NotImplementedError(f'len({hits=}) != 2')

        (c0, s0), (c1, s1) = sorted(hits)
        if c0 == c1:
            # creating an interior space
            c = c0
            v = self.curves[c]
            new_points = []
            new_bases = []
            fb = v.bases[s0 - 1]

            new_bases.extend(v.bases[:s0])
            new_points.extend(v.points[:s0])
            new_points.extend(v.points[s1:])
            new_bases.append(fb)
            new_bases.extend(v.bases[s1 + 1:])

            interior_points = v.points[s0:s1]
            interior_bases = v.bases[s0:s1]

            return BoundaryList([
                *self.curves[:c],
                Curve(points=new_points, bases=new_bases),
                *self.curves[c + 1:],
                Curve(points=interior_points, bases=interior_bases),
            ])
        else:
            # stitching two regions
            v0 = self.curves[c0]
            v1 = self.curves[c1]
            new_points = []
            new_bases = []
            fb = v0.bases[s0 - 1]

            new_bases.extend(v0.bases[:s0])
            new_points.extend(v0.points[:s0])

            new_points.extend(v1.points[s1:])
            new_bases.append(fb)
            new_bases.extend(v1.bases[s1 + 1:])

            new_points.extend(v1.points[:s1])
            new_bases.extend(v1.bases[:s1])

            new_points.extend(v0.points[s0:])
            new_bases.append(fb)
            new_bases.extend(v0.bases[s0 + 1:])

            return BoundaryList([
                *self.curves[:c0],
                Curve(points=new_points, bases=new_bases),
                *self.curves[c0 + 1:c1],
                *self.curves[c1 + 1:],
            ])

    def to_plan(
        self,
        *,
        rel_order_func: Callable[[complex], Iterable[complex]],
    ) -> Patch:
        """Converts the boundary list into an explicit surface code stabilizer configuration."""

        data_qubits = self.interior(include_boundary=True)
        contiguous_x_data_qubit_sets = []
        contiguous_z_data_qubit_sets = []
        for c in self.curves:
            cur_set = None
            for k in range(len(c.points)):
                if k == 0 or c.bases[k] != c.bases[k - 1]:
                    cur_set = set()
                    if c.bases[k] == 'X':
                        contiguous_x_data_qubit_sets.append(cur_set)
                    else:
                        contiguous_z_data_qubit_sets.append(cur_set)
                a = c.points[k - 1]
                b = c.points[k]
                for p in int_points_on_line(a, b):
                    cur_set.add(p)

        internal_measure_qubits = half_int_points_inside_int_polygon_set(
            curves=[curve.points for curve in self.curves],
            include_boundary=True,
        )

        plaqs = []
        external_measure_qubits = set()
        for c in self.curves:
            b = c.boundary_travel()
            b3 = b * 3
            n = len(b)
            for k in range(n):
                nearby_measurement_qubits = {b[k] + d for d in Order_Z}
                for m in nearby_measurement_qubits:
                    if m in internal_measure_qubits:
                        continue
                    if m in external_measure_qubits:
                        continue
                    relevant_contiguous_sets = contiguous_z_data_qubit_sets if checkerboard_basis(m) == 'Z' else contiguous_x_data_qubit_sets
                    nearby_boundary_data = b3[n+k-2:n+k+3]
                    ds = set()
                    for contiguous_candidate in relevant_contiguous_sets:
                        kept_ds = {m + d for d in Order_Z if m + d in nearby_boundary_data and m + d in contiguous_candidate}
                        if len(kept_ds) > len(ds):
                            ds = kept_ds
                    if len(ds) < 2:
                        continue
                    plaqs.append(Tile(
                        bases=checkerboard_basis(m),
                        measurement_qubit=m,
                        ordered_data_qubits=[m + d if d is not None and m + d in ds else None for d in rel_order_func(m)]
                    ))
                    external_measure_qubits.add(m)

        d_count = collections.Counter()
        for m in internal_measure_qubits:
            for d in Order_Z:
                d_count[m + d] += 1
        for p in plaqs:
            # Don't trim data qubits used by boundary measurements.
            for d in p.data_set:
                d_count[d] += 100

        used_data_qubits = set()
        for d in sorted_complex(data_qubits):
            if d_count[d] > 1:
                used_data_qubits.add(d)

        for m in internal_measure_qubits:
            b = checkerboard_basis(m)
            plaqs.append(Tile(
                bases=b,
                measurement_qubit=m,
                ordered_data_qubits=[m + d if d is not None and m + d in used_data_qubits else None for d in rel_order_func(m)],
            ))

        return Patch(plaqs)

    def __eq__(self, other):
        if not isinstance(other, BoundaryList):
            return NotImplemented
        return self.curves == other.curves

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return f'BoundaryList(curves={self.curves!r})'


def int_points_on_line(a: complex, b: complex) -> List[complex]:
    """Lists the integer points along a given line segment.

    The delta `a-b` must be horizontal (imaginary part is 0), vertical
    (real part is 0), or diagonal (real and imaginary parts have same
    absolute magnitude).

    Args:
        a: A complex number with integer real part and integer imaginary part.
        b: A complex number with integer real part and integer imaginary part.

    Returns:
        The list of integer points.
    """
    dr = b.real - a.real
    di = b.imag - a.imag
    if a == b:
        return [a]
    if len({0, abs(di), abs(dr)}) != 2:
        raise NotImplementedError(f"{a=} to {b=} isn't horizontal, vertical, or 1:1 diagonal.")
    steps = int(max(abs(dr), abs(di)))
    result = []
    dr /= steps
    di /= steps
    assert int(dr) == dr
    assert int(di) == di
    dr = int(dr)
    di = int(di)
    for k in range(steps + 1):
        result.append(a + dr*k + di*k*1j)
    return result


def int_travel_points_on_polygon_boundary(corners: List[complex]) -> List[complex]:
    boundary = []
    for k in range(len(corners)):
        a = corners[k - 1]
        b = corners[k]
        for p in int_points_on_line(a, b):
            if len(boundary) == 0 or boundary[-1] != p:
                boundary.append(p)
    assert boundary[-1] == boundary[0]
    boundary.pop()
    return boundary


def half_int_points_inside_int_polygon_set(*,
                                           curves: List[List[complex]],
                                           include_boundary: bool,
                                           match_mask: Optional[int] = None) -> Set[complex]:
    curves2 = [[pt * 2 for pt in curve] for curve in curves]
    interior2 = int_points_inside_polygon_set(curves2, include_boundary=include_boundary, match_mask=match_mask)
    return {p / 2 for p in interior2 if p.real % 2 == 1 and p.imag % 2 == 1}


def half_int_points_inside_int_polygon(corners: List[complex], *, include_boundary: bool) -> Set[complex]:
    return half_int_points_inside_int_polygon_set(curves=[corners], include_boundary=include_boundary)


def int_points_inside_polygon(corners: List[complex], *, include_boundary: bool) -> Set[complex]:
    return int_points_inside_polygon_set([corners], include_boundary=include_boundary)


def int_points_inside_polygon_set(
        curves: Iterable[List[complex]],
        *,
        include_boundary: bool,
        match_mask: Optional[int] = None,
) -> Set[complex]:
    curves = tuple(curves)
    min_real = int(min(pt.real for curve in curves for pt in curve))
    min_imag = int(min(pt.imag for curve in curves for pt in curve))
    max_real = int(max(pt.real for curve in curves for pt in curve))
    max_imag = int(max(pt.imag for curve in curves for pt in curve))

    boundary = set()
    half_boundary = collections.defaultdict(int)
    for k, curve in enumerate(curves):
        boundary |= set(int_travel_points_on_polygon_boundary(curve))
        for p in set(int_travel_points_on_polygon_boundary([p * 2 for p in curve])):
            half_boundary[p / 2] ^= 1 << k

    result = set()
    for r in range(min_real, max_real + 1):
        r0 = r - 0.5
        r1 = r + 0.5
        mask0 = 0
        inside0 = 0
        mask1 = 0
        inside1 = 0
        i = min_imag
        while i <= max_imag:
            c0 = r0 + i * 1j
            c1 = r1 + i * 1j
            inside0 ^= half_boundary[c0] != 0
            inside1 ^= half_boundary[c1] != 0
            mask0 ^= half_boundary[c0]
            mask1 ^= half_boundary[c1]
            m0 = mask0 if inside0 else 0
            m1 = mask1 if inside1 else 0
            if i == int(i) and m0 == m1 and (m0 != 0 if match_mask is None else m0 == match_mask):
                result.add(r + i * 1j)
            i += 0.5

    if include_boundary:
        result |= boundary
    else:
        result -= boundary

    return result


def int_point_disjoint_regions_inside_polygon_set(
        curves: Iterable[List[complex]],
        *,
        include_boundary: bool) -> Dict[int, Set[complex]]:
    curves = tuple(curves)
    min_real = int(min(pt.real for curve in curves for pt in curve))
    min_imag = int(min(pt.imag for curve in curves for pt in curve))
    max_real = int(max(pt.real for curve in curves for pt in curve))
    max_imag = int(max(pt.imag for curve in curves for pt in curve))

    half_boundary = collections.defaultdict(int)
    for k, curve in enumerate(curves):
        for p in set(int_travel_points_on_polygon_boundary([p * 2 for p in curve])):
            half_boundary[p / 2] ^= 1 << k

    result = collections.defaultdict(set)
    for r in range(min_real, max_real + 1):
        r0 = r - 0.5
        r1 = r + 0.5

        mask0 = 0
        mask1 = 0
        inside0 = 0
        inside1 = 0
        i = min_imag
        while i <= max_imag:
            c0 = r0 + i * 1j
            c1 = r1 + i * 1j
            c = r + i * 1j
            b0 = half_boundary[c0]
            b1 = half_boundary[c1]
            new_inside0 = inside0 ^ (b0 != 0)
            new_inside1 = inside1 ^ (b1 != 0)
            new_mask0 = mask0 ^ b0
            new_mask1 = mask1 ^ b1
            if i == int(i):
                if include_boundary:
                    # On horizontal segment?
                    if inside0 and not new_inside0:
                        result[mask0].add(c)
                    if not inside0 and new_inside0:
                        result[new_mask0].add(c)
                    if inside1 and not new_inside1:
                        result[mask1].add(c)
                    if not inside1 and new_inside1:
                        result[new_mask1].add(c)

                    # On vertical segment?
                    if inside0 and not inside1:
                        result[mask0].add(c)
                    if new_inside0 and not new_inside1:
                        result[new_mask0].add(c)
                    if inside1 and not inside0:
                        result[mask1].add(c)
                    if new_inside1 and not new_inside0:
                        result[new_mask1].add(c)
                if inside0 and inside1 and new_inside0 and new_inside1 and mask0 == mask1 == new_mask0 == new_mask1:
                    # Interior.
                    result[mask0].add(c)
            mask0 = new_mask0
            mask1 = new_mask1
            inside0 = new_inside0
            inside1 = new_inside1
            i += 0.5

    if 0 in result:
        del result[0]

    return dict(result)
