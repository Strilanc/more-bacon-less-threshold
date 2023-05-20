import pytest

from gen._boundary_list import int_points_on_line, int_points_inside_polygon, \
    half_int_points_inside_int_polygon, Curve, \
    BoundaryList, int_point_disjoint_regions_inside_polygon_set, Order_ᴎ, checkerboard_basis, Order_Z
from gen._util import sorted_complex


def test_int_points_on_line():
    with pytest.raises(NotImplementedError):
        int_points_on_line(0, 1 + 2j)

    assert int_points_on_line(0, 0) == [0]
    assert int_points_on_line(0, 5) == [0, 1, 2, 3, 4, 5]
    assert int_points_on_line(1, -3) == [1, 0, -1, -2, -3]
    assert int_points_on_line(1j, 3j) == [1j, 2j, 3j]
    assert int_points_on_line(0, -2j) == [0, -1j, -2j]
    assert int_points_on_line(5, 8 + 3j) == [5, 6 + 1j, 7 + 2j, 8 + 3j]
    assert int_points_on_line(5, 8 - 3j) == [5, 6 - 1j, 7 - 2j, 8 - 3j]
    assert int_points_on_line(5, 2 + 3j) == [5, 4 + 1j, 3 + 2j, 2 + 3j]
    assert int_points_on_line(5, 2 - 3j) == [5, 4 - 1j, 3 - 2j, 2 - 3j]


def test_tight_boundary():
    c1 = Curve()
    c1.line_to('Z', 5 + 0j)
    c1.line_to('X', 5 + 3j)
    c1.line_to('Z', 0 + 3j)
    c1.line_to('X', 0 + 0j)

    c2 = Curve()
    c2.line_to('X', 5 + 4j)
    c2.line_to('X', 5 + 6j)
    c2.line_to('X', 0 + 6j)
    c2.line_to('X', 0 + 4j)

    b = BoundaryList([c1, c2])
    fused = b.fused(c1.med(), c2.med())

    c3 = Curve()
    c3.line_to('Z', 5 + 0j)
    c3.line_to('X', 5 + 3j)
    c3.line_to('X', 5 + 4j)
    c3.line_to('X', 5 + 6j)
    c3.line_to('X', 0 + 6j)
    c3.line_to('X', 0 + 4j)
    c3.line_to('X', 0 + 3j)
    c3.line_to('X', 0 + 0j)
    assert fused == BoundaryList([c3])

    p = b.to_plan(rel_order_func=lambda m: Order_Z if checkerboard_basis(m) == 'Z' else Order_ᴎ)
    assert sum(e.basis == 'X' and len(e.data_set) == 2 for e in p.tiles) == 11
    assert sum(e.basis == 'Z' and len(e.data_set) == 2 for e in p.tiles) == 4


def test_pitchfork_boundary():
    b = BoundaryList([
        Curve(points=[0, 3, 3 + 10j, 2 + 10j, 2 + 6j, 1 + 6j, 1 + 10j, 10j],
              bases='XXXXZXXX'),
    ])
    p = b.to_plan(rel_order_func=lambda m: Order_Z if checkerboard_basis(m) == 'Z' else Order_ᴎ)

    assert sum(e.basis == 'X' and len(e.data_set) == 2 for e in p.tiles) == 15
    assert sum(e.basis == 'X' and len(e.data_set) == 3 for e in p.tiles) == 1
    assert sum(e.basis == 'Z' and len(e.data_set) == 2 for e in p.tiles) == 2
    assert sum(e.basis == 'Z' and len(e.data_set) == 3 for e in p.tiles) == 0


def test_line():
    c = Curve()
    c.line_to('Z', 6)
    c.line_to('X', 6)
    c.line_to('Z', 0)
    c.line_to('X', 0)
    b = BoundaryList([c])
    p = b.to_plan(rel_order_func=lambda m: Order_Z if checkerboard_basis(m) == 'Z' else Order_ᴎ)
    assert p.data_set == {0, 1, 2, 3, 4, 5, 6}
    assert p.measure_set == {0.5 + 0.5j, 1.5 - 0.5j, 2.5 + 0.5j, 3.5 - 0.5j, 4.5 + 0.5j, 5.5 - 0.5j}
    assert all(len(e.data_set) == 2 for e in p.tiles)
    assert len(p.tiles) == 6


def test_hole():
    c = Curve()
    c.line_to('Z', 0)
    c.line_to('X', 10)
    c.line_to('Z', 10 + 10j)
    c.line_to('X', 10j)

    c2 = Curve()
    c2.line_to('X', 2 + 2j)
    c2.line_to('X', 8 + 2j)
    c2.line_to('X', 8 + 8j)
    c2.line_to('X', 2 + 8j)

    b = BoundaryList([c, c2])
    p = b.to_plan(rel_order_func=lambda m: Order_Z if checkerboard_basis(m) == 'Z' else Order_ᴎ)
    assert sum(e.basis == 'X' and len(e.data_set) == 2 for e in p.tiles) == 18
    assert sum(e.basis == 'Z' and len(e.data_set) == 2 for e in p.tiles) == 10
    assert sum(e.basis == 'X' and len(e.data_set) == 3 for e in p.tiles) == 2
    assert sum(e.basis == 'Z' and len(e.data_set) == 3 for e in p.tiles) == 0


def test_int_points_inside_polygon():
    assert sorted_complex(int_points_inside_polygon([0, 3, 3+2j, 5j], include_boundary=True)) == [
        0 + 0j, 0 + 1j, 0 + 2j, 0 + 3j, 0 + 4j, 0 + 5j,
        1 + 0j, 1 + 1j, 1 + 2j, 1 + 3j, 1 + 4j,
        2 + 0j, 2 + 1j, 2 + 2j, 2 + 3j,
        3 + 0j, 3 + 1j, 3 + 2j,
    ]
    assert sorted_complex(int_points_inside_polygon([0, 3, 3+2j, 5j], include_boundary=False)) == [
        1 + 1j, 1 + 2j, 1 + 3j,
        2 + 1j, 2 + 2j,
    ]


def test_half_int_points_inside_int_polygon():
    assert sorted_complex(half_int_points_inside_int_polygon([0, 3, 3+2j, 5j], include_boundary=True)) == [
        0.5 + 0.5j, 0.5 + 1.5j, 0.5 + 2.5j, 0.5 + 3.5j, 0.5 + 4.5j,
        1.5 + 0.5j, 1.5 + 1.5j, 1.5 + 2.5j, 1.5 + 3.5j,
        2.5 + 0.5j, 2.5 + 1.5j, 2.5 + 2.5j,
    ]
    assert sorted_complex(half_int_points_inside_int_polygon([0, 3, 3+2j, 5j], include_boundary=False)) == [
        0.5 + 0.5j, 0.5 + 1.5j, 0.5 + 2.5j, 0.5 + 3.5j,
        1.5 + 0.5j, 1.5 + 1.5j, 1.5 + 2.5j,
        2.5 + 0.5j, 2.5 + 1.5j,
    ]


def test_fused_simple():
    a = Curve()
    a.line_to('X', 4 + 0j)
    a.line_to('Z', 4 + 4j)
    a.line_to('X', 0 + 4j)
    a.line_to('Z', 0 + 0j)

    b = BoundaryList(curves=[a, a.offset_by(6)])
    b = b.fused(2 + 2j, 8 + 2j)
    assert b == BoundaryList(curves=[
        Curve(
            points=[4 + 0j, 6 + 0j, 10 + 0j, 10 + 4j, 6 + 4j, 4 + 4j, 0 + 4j, 0 + 0j],
            bases=['X', 'X', 'X', 'Z', 'X', 'X', 'X', 'Z'],
        ),
    ])


def test_fused_stability():
    a = Curve()
    a.line_to('Z', 4 + 0j)
    a.line_to('Z', 4 + 4j)
    a.line_to('Z', 0 + 4j)
    a.line_to('Z', 0 + 0j)

    b = BoundaryList(curves=[a, a.offset_by(6j), a.offset_by(12j)])
    b = b.fused(2 + 2j, 2 + 8j)
    assert b == BoundaryList(curves=[
        Curve(
            points=[4 + 0j, 4 + 4j, 4 + 6j, 4 + 10j, 0 + 10j, 0 + 6j, 0 + 4j, 0 + 0j],
            bases=['Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z'],
        ),
        a.offset_by(12j),
    ])

    b = b.fused(2 + 8j, 2 + 14j)
    assert b == BoundaryList(curves=[
        Curve(
            points=[4 + 0j, 4 + 4j, 4 + 6j, 4 + 10j, 4 + 12j, 4 + 16j, 0 + 16j, 0 + 12j, 0 + 10j, 0 + 6j, 0 + 4j, 0 + 0j],
            bases=['Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z'],
        ),
    ])


def test_fused_t():
    a = Curve()
    a.line_to('Z', 4 + 0j)
    a.line_to('Z', 4 + 4j)
    a.line_to('Z', 0 + 4j)
    a.line_to('Z', 0 + 0j)

    b = BoundaryList(curves=[a, a.offset_by(6j), a.offset_by(6j - 6)])
    b = b.fused(2 + 2j, 2 + 8j)
    assert b == BoundaryList(curves=[
        Curve(
            points=[4 + 0j, 4 + 4j, 4 + 6j, 4 + 10j, 0 + 10j, 0 + 6j, 0 + 4j, 0 + 0j],
            bases=['Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z'],
        ),
        a.offset_by(6j - 6),
    ])

    b = b.fused(-4 + 8j, 2 + 8j)
    assert b == BoundaryList(curves=[
        Curve(
            points=[4 + 0j, 4 + 4j, 4 + 6j, 4 + 10j, 0 + 10j, -2 + 10j, -6 + 10j, -6 + 6j, -2 + 6j, 0 + 6j, 0 + 4j, 0 + 0j],
            bases=['Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z'],
        ),
    ])
    assert len([p for p in int_points_inside_polygon(b.curves[0].points, include_boundary=False) if p.real == 0]) == 3


def test_fused_interior():
    a = Curve()
    a.line_to('Z', 12 + 0j)
    a.line_to('Z', 12 + 4j)
    a.line_to('Z', 8 + 4j)
    a.line_to('Z', 4 + 4j)
    a.line_to('Z', 4 + 8j)
    a.line_to('Z', 8 + 8j)
    a.line_to('Z', 12 + 8j)
    a.line_to('Z', 12 + 12j)
    a.line_to('Z', 0 + 12j)
    a.line_to('Z', 0)

    actual = BoundaryList(curves=[a]).fused(10 + 2j, 10 + 10j)
    assert actual == BoundaryList(curves=[
        Curve(
            points=[(12+0j), (12+4j), (12+8j), (12+12j), 12j, 0],
            bases=['Z', 'Z', 'Z', 'Z', 'Z', 'Z'],
        ),
        Curve(
            points=[(8+4j), (4+4j), (4+8j), (8+8j)],
            bases=['Z', 'Z', 'Z', 'Z'],
        ),
    ])


def test_fused_inner():
    b1 = BoundaryList([Curve(
        points=[
            0+16j, 6+16j, 8+16j, 14+16j, 16+16j, 22+16j,
            22+18j, 22+20j, 22+22j, 22+24j, 22+26j, 22+28j, 22+30j,
            16+30j, 16+28j, 16+26j,
            14+26j, 8+26j,
            8+24j, 14+24j, 16+24j,
            16+22j, 16+20j, 16+18j,
            14+18j, 8+18j, 6+18j,
            6+20j, 8+20j, 14+20j,
            14+22j, 8+22j, 6+22j,
            6+24j, 6+26j, 6+28j,
            8+28j, 14+28j,
            14+30j, 8+30j, 6+30j,
            30j, 28j, 26j, 24j, 22j, 20j, 18j,
        ],
        bases='XXXXXXXXXXXXXXXXXXZXXXXXXXXXXXZXXXXXXXZXXXXXXXXX'
    )])
    b2 = b1.fused(19+29j, 11+29j)

    assert len(b2.curves) == 2
    assert all(e == 'X' for e in b2.curves[0].bases)
    assert b2.curves[1] == Curve(
        points=[
            (16+28j), (16+26j),
            (14+26j), (8+26j),
            (8+24j), (14+24j), (16+24j),
            (16+22j), (16+20j), (16+18j),
            (14+18j), (8+18j), (6+18j),
            (6+20j), (8+20j), (14+20j),
            (14+22j), (8+22j), (6+22j),
            (6+24j), (6+26j), (6+28j),
            (8+28j), (14+28j),
        ],
        bases='XXXXZXXXXXXXXXXXZXXXXXXX',
    )


def test_int_point_disjoint_regions_inside_polygon_set():
    a = int_point_disjoint_regions_inside_polygon_set([
        [0, 3, 3+2j, 2j],
        [3j, 3 + 3j, 3+5j, 5j],
    ], include_boundary=False)
    assert len(a) == 2
    assert a[1] == {1 + 1j, 2 + 1j}
    assert a[2] == {1 + 4j, 2 + 4j}

    a = int_point_disjoint_regions_inside_polygon_set([
        [0, 3, 3+2j, 2j],
        [3j, 3 + 3j, 3+5j, 5j],
    ], include_boundary=True)
    assert len(a) == 2
    assert a[1] == {0, 1, 2, 3,
                    0 + 1j, 1 + 1j, 2 + 1j, 3 + 1j,
                    0 + 2j, 1 + 2j, 2 + 2j, 3 + 2j}
    assert a[2] == {0 + 3j, 1 + 3j, 2 + 3j, 3 + 3j,
                    0 + 4j, 1 + 4j, 2 + 4j, 3 + 4j,
                    0 + 5j, 1 + 5j, 2 + 5j, 3 + 5j}
