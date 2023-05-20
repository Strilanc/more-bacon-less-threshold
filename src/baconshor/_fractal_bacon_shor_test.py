import itertools
from typing import Set, Tuple

import pytest
import stim

import gen
from baconshor._fractal_bacon_shor import \
    fractal_bacon_shor_detector_ranges, make_bacon_shor_fractal_circuit, is_parity_measurement_active


def _l(k: int, f: int) -> int:
    t = 0
    while k % f == 0 and k:
        k //= f
        t += 1
    return t


def test_is_parity_measurement_active_simplified():
    dt = 80
    ds = 40
    f = 3
    for e in range(1, ds + 1):
        for step in range(dt)[-1:]:
            actual = is_parity_measurement_active(
                divider_index=e - 1,
                time_step=step,
                phase1=0,
                phase2=2,
                space_d=f,
                time_d=1,
            )
            b = (0 if e % 2 == 0 else 2)
            numer, modulus = _inc_pattern(b=b, e=e, f=f)
            expected = any((s % modulus) == (numer % modulus) for s in range(step*4, step*4 + 4))
            assert expected == actual


def _inc_pattern(*, b: int, e: int, f: int) -> Tuple[int, int]:
    l = _l(e, f) + 1
    numer = b * (4 ** l - 1) // 3
    modulus = 4 ** l
    return numer, modulus


def test_is_parity_measurement_active_simplified_exact():
    f = 5

    vals = []
    for e in range(1, 27):
        b = (2 if e % 2 == 0 else 0)
        vals.append(_inc_pattern(b=b, f=f, e=e))
    assert vals == [
        (0, 4),
        (2, 4),
        (0, 4),
        (2, 4),
        (0, 16),
        (2, 4),
        (0, 4),
        (2, 4),
        (0, 4),
        (10, 16),
        (0, 4),
        (2, 4),
        (0, 4),
        (2, 4),
        (0, 16),
        (2, 4),
        (0, 4),
        (2, 4),
        (0, 4),
        (10, 16),
        (0, 4),
        (2, 4),
        (0, 4),
        (2, 4),
        (0, 64),
        (2, 4),
    ]

    vals = []
    for e in range(1, 27):
        b = (3 if e % 2 == 0 else 1)
        vals.append(_inc_pattern(b=b, f=f, e=e))
    assert vals == [
        (1, 4),
        (3, 4),
        (1, 4),
        (3, 4),
        (5, 16),
        (3, 4),
        (1, 4),
        (3, 4),
        (1, 4),
        (15, 16),
        (1, 4),
        (3, 4),
        (1, 4),
        (3, 4),
        (5, 16),
        (3, 4),
        (1, 4),
        (3, 4),
        (1, 4),
        (15, 16),
        (1, 4),
        (3, 4),
        (1, 4),
        (3, 4),
        (21, 64),
        (3, 4),
    ]


def test_is_parity_measurement_active():
    dt = 80
    ds = 20
    rows = []
    rows.append('\n        ' + '.' * dt)
    for k in range(ds):
        row = []
        for step in range(dt):
            row.append(is_parity_measurement_active(divider_index=k, time_step=step, phase1=0, phase2=2, space_d=3, time_d=2))
        rows.append('\n        ' + ''.join(' |'[e] for e in row) + '')
        rows.append('\n        ' + '.' * dt)
    actual = ''.join(rows) + '\n    '
    assert actual == """
        ................................................................................
        ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
        ................................................................................
        ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
        ................................................................................
            ||      ||      ||      ||      ||      ||      ||      ||      ||      ||  
        ................................................................................
        ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
        ................................................................................
        ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
        ................................................................................
        ||      ||      ||      ||      ||      ||      ||      ||      ||      ||      
        ................................................................................
        ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
        ................................................................................
        ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
        ................................................................................
                                            ||      ||                                  
        ................................................................................
        ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
        ................................................................................
        ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
        ................................................................................
        ||      ||      ||      ||      ||      ||      ||      ||      ||      ||      
        ................................................................................
        ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
        ................................................................................
        ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
        ................................................................................
            ||      ||      ||      ||      ||      ||      ||      ||      ||      ||  
        ................................................................................
        ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
        ................................................................................
        ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
        ................................................................................
        ||      ||                                                      ||      ||      
        ................................................................................
        ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
        ................................................................................
        ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
        ................................................................................
    """


def test_fractal_bacon_shor_detector_ranges():
    line_cuts: Set[complex] = set()

    assert fractal_bacon_shor_detector_ranges(
        line_top_left=0,
        line_dir=1j,
        span=5,
        line_cuts_inplace_edit=line_cuts,
    ) == [[0.5], [0.5 + 1j], [0.5 + 2j], [0.5 + 3j], [0.5 + 4j]]
    assert line_cuts == set()

    line_cuts.add(0.5 + 2.5j)
    line_cuts.add(1.5 + 1.5j)
    assert fractal_bacon_shor_detector_ranges(
        line_top_left=0,
        line_dir=1j,
        span=5,
        line_cuts_inplace_edit=line_cuts,
    ) == [[0.5], [0.5 + 1j], [0.5 + 2j, 0.5 + 3j], [0.5 + 4j]]
    assert line_cuts == {1.5 + 1.5j}

    assert fractal_bacon_shor_detector_ranges(
        line_top_left=1j,
        line_dir=1,
        span=5,
        line_cuts_inplace_edit=line_cuts,
    ) == [[1.5j], [1+1.5j, 2+1.5j], [3+1.5j], [4+1.5j]]
    assert line_cuts == set()


@pytest.mark.parametrize('width,height,basis,rounds', itertools.product(
    [4, 16],
    [6, 12],
    ['X', 'Z'],
    [1, 5, 24],
))
def test_make_fractal_circuit(width: int, height: int, basis: str, rounds: int):
    circuit = make_bacon_shor_fractal_circuit(
        width=width,
        height=height,
        rounds=rounds,
        basis=basis,
        fractal_pitch=3,
        surgery_hold_factor=2,
    )
    circuit = gen.NoiseModel.uniform_depolarizing(1e-3).noisy_circuit(circuit)

    assert circuit.num_ticks == rounds * 4 + 1

    # Some detectors are missed when the patch fails to completely fuse in the small number of rounds given.
    missed = width * height if rounds > max(width, height) else 0
    assert gen.count_determined_measurements_in_circuit(circuit) >= circuit.num_detectors + circuit.num_observables - missed

    expected_distance = width // 2 if basis == 'X' else height // 2
    assert len(circuit.shortest_graphlike_error()) >= expected_distance

    assert gen.gates_used_by_circuit(circuit) <= {
        'R',
        'M',
        'RX',
        'MX',
        'MXX',
        'MZZ',

        'TICK',
        'DEPOLARIZE1',
        'DEPOLARIZE2',
        'DETECTOR',
        'X_ERROR',
        'Z_ERROR',
        'OBSERVABLE_INCLUDE',
        'QUBIT_COORDS',
        'SHIFT_COORDS',
    }


def test_exact_circuit():
    width = 6
    height = 6
    basis = 'X'
    rounds = 10
    circuit = make_bacon_shor_fractal_circuit(
        width=width,
        height=height,
        basis=basis,
        rounds=rounds,
        fractal_pitch=3,
        surgery_hold_factor=1,
    )
    assert circuit == stim.Circuit("""
        QUBIT_COORDS(0, 0) 0
        QUBIT_COORDS(0, 1) 1
        QUBIT_COORDS(0, 2) 2
        QUBIT_COORDS(0, 3) 3
        QUBIT_COORDS(0, 4) 4
        QUBIT_COORDS(0, 5) 5
        QUBIT_COORDS(1, 0) 6
        QUBIT_COORDS(1, 1) 7
        QUBIT_COORDS(1, 2) 8
        QUBIT_COORDS(1, 3) 9
        QUBIT_COORDS(1, 4) 10
        QUBIT_COORDS(1, 5) 11
        QUBIT_COORDS(2, 0) 12
        QUBIT_COORDS(2, 1) 13
        QUBIT_COORDS(2, 2) 14
        QUBIT_COORDS(2, 3) 15
        QUBIT_COORDS(2, 4) 16
        QUBIT_COORDS(2, 5) 17
        QUBIT_COORDS(3, 0) 18
        QUBIT_COORDS(3, 1) 19
        QUBIT_COORDS(3, 2) 20
        QUBIT_COORDS(3, 3) 21
        QUBIT_COORDS(3, 4) 22
        QUBIT_COORDS(3, 5) 23
        QUBIT_COORDS(4, 0) 24
        QUBIT_COORDS(4, 1) 25
        QUBIT_COORDS(4, 2) 26
        QUBIT_COORDS(4, 3) 27
        QUBIT_COORDS(4, 4) 28
        QUBIT_COORDS(4, 5) 29
        QUBIT_COORDS(5, 0) 30
        QUBIT_COORDS(5, 1) 31
        QUBIT_COORDS(5, 2) 32
        QUBIT_COORDS(5, 3) 33
        QUBIT_COORDS(5, 4) 34
        QUBIT_COORDS(5, 5) 35
        RX 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35
        TICK
        MPP X0*X6 X1*X7 X2*X8 X3*X9 X4*X10 X5*X11 X24*X30 X25*X31 X26*X32 X27*X33 X28*X34 X29*X35
        DETECTOR(0.5, 0, 0, 1) rec[-12]
        DETECTOR(0.5, 1, 0, 1) rec[-11]
        DETECTOR(0.5, 2, 0, 1) rec[-10]
        DETECTOR(0.5, 3, 0, 1) rec[-9]
        DETECTOR(0.5, 4, 0, 1) rec[-8]
        DETECTOR(0.5, 5, 0, 1) rec[-7]
        DETECTOR(4.5, 0, 0, 1) rec[-6]
        DETECTOR(4.5, 1, 0, 1) rec[-5]
        DETECTOR(4.5, 2, 0, 1) rec[-4]
        DETECTOR(4.5, 3, 0, 1) rec[-3]
        DETECTOR(4.5, 4, 0, 1) rec[-2]
        DETECTOR(4.5, 5, 0, 1) rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP X6*X12 X7*X13 X8*X14 X9*X15 X10*X16 X11*X17 X18*X24 X19*X25 X20*X26 X21*X27 X22*X28 X23*X29
        DETECTOR(1.5, 0, 0, 1) rec[-12]
        DETECTOR(1.5, 1, 0, 1) rec[-11]
        DETECTOR(1.5, 2, 0, 1) rec[-10]
        DETECTOR(1.5, 3, 0, 1) rec[-9]
        DETECTOR(1.5, 4, 0, 1) rec[-8]
        DETECTOR(1.5, 5, 0, 1) rec[-7]
        DETECTOR(3.5, 0, 0, 1) rec[-6]
        DETECTOR(3.5, 1, 0, 1) rec[-5]
        DETECTOR(3.5, 2, 0, 1) rec[-4]
        DETECTOR(3.5, 3, 0, 1) rec[-3]
        DETECTOR(3.5, 4, 0, 1) rec[-2]
        DETECTOR(3.5, 5, 0, 1) rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP Z0*Z1 Z4*Z5 Z6*Z7 Z10*Z11 Z12*Z13 Z16*Z17 Z18*Z19 Z22*Z23 Z24*Z25 Z28*Z29 Z30*Z31 Z34*Z35
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP Z1*Z2 Z3*Z4 Z7*Z8 Z9*Z10 Z13*Z14 Z15*Z16 Z19*Z20 Z21*Z22 Z25*Z26 Z27*Z28 Z31*Z32 Z33*Z34
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP X0*X6 X1*X7 X2*X8 X3*X9 X4*X10 X5*X11 X24*X30 X25*X31 X26*X32 X27*X33 X28*X34 X29*X35
        DETECTOR(0.5, 0, 0, 1) rec[-60] rec[-59] rec[-58] rec[-12] rec[-11] rec[-10]
        DETECTOR(0.5, 3, 0, 1) rec[-57] rec[-56] rec[-55] rec[-9] rec[-8] rec[-7]
        DETECTOR(4.5, 0, 0, 1) rec[-54] rec[-53] rec[-52] rec[-6] rec[-5] rec[-4]
        DETECTOR(4.5, 3, 0, 1) rec[-51] rec[-50] rec[-49] rec[-3] rec[-2] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP X6*X12 X7*X13 X8*X14 X9*X15 X10*X16 X11*X17 X18*X24 X19*X25 X20*X26 X21*X27 X22*X28 X23*X29
        DETECTOR(1.5, 0, 0, 1) rec[-60] rec[-59] rec[-58] rec[-12] rec[-11] rec[-10]
        DETECTOR(1.5, 3, 0, 1) rec[-57] rec[-56] rec[-55] rec[-9] rec[-8] rec[-7]
        DETECTOR(3.5, 0, 0, 1) rec[-54] rec[-53] rec[-52] rec[-6] rec[-5] rec[-4]
        DETECTOR(3.5, 3, 0, 1) rec[-51] rec[-50] rec[-49] rec[-3] rec[-2] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP Z0*Z1 Z4*Z5 Z6*Z7 Z10*Z11 Z12*Z13 Z16*Z17 Z18*Z19 Z22*Z23 Z24*Z25 Z28*Z29 Z30*Z31 Z34*Z35
        DETECTOR(10, 0.5, 0, 2) rec[-60] rec[-58] rec[-56] rec[-12] rec[-10] rec[-8]
        DETECTOR(13, 0.5, 0, 2) rec[-54] rec[-52] rec[-50] rec[-6] rec[-4] rec[-2]
        DETECTOR(10, 4.5, 0, 2) rec[-59] rec[-57] rec[-55] rec[-11] rec[-9] rec[-7]
        DETECTOR(13, 4.5, 0, 2) rec[-53] rec[-51] rec[-49] rec[-5] rec[-3] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP Z1*Z2 Z3*Z4 Z7*Z8 Z9*Z10 Z13*Z14 Z15*Z16 Z19*Z20 Z21*Z22 Z25*Z26 Z27*Z28 Z31*Z32 Z33*Z34
        DETECTOR(10, 1.5, 0, 2) rec[-60] rec[-58] rec[-56] rec[-12] rec[-10] rec[-8]
        DETECTOR(13, 1.5, 0, 2) rec[-54] rec[-52] rec[-50] rec[-6] rec[-4] rec[-2]
        DETECTOR(10, 3.5, 0, 2) rec[-59] rec[-57] rec[-55] rec[-11] rec[-9] rec[-7]
        DETECTOR(13, 3.5, 0, 2) rec[-53] rec[-51] rec[-49] rec[-5] rec[-3] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP X0*X6 X1*X7 X2*X8 X3*X9 X4*X10 X5*X11 X12*X18 X13*X19 X14*X20 X15*X21 X16*X22 X17*X23 X24*X30 X25*X31 X26*X32 X27*X33 X28*X34 X29*X35
        DETECTOR(0.5, 0, 0, 1) rec[-66] rec[-65] rec[-64] rec[-18] rec[-17] rec[-16]
        DETECTOR(0.5, 3, 0, 1) rec[-63] rec[-62] rec[-61] rec[-15] rec[-14] rec[-13]
        DETECTOR(2.5, 0, 0, 1) rec[-12] rec[-11] rec[-10]
        DETECTOR(2.5, 3, 0, 1) rec[-9] rec[-8] rec[-7]
        DETECTOR(4.5, 0, 0, 1) rec[-60] rec[-59] rec[-58] rec[-6] rec[-5] rec[-4]
        DETECTOR(4.5, 3, 0, 1) rec[-57] rec[-56] rec[-55] rec[-3] rec[-2] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP X6*X12 X7*X13 X8*X14 X9*X15 X10*X16 X11*X17 X18*X24 X19*X25 X20*X26 X21*X27 X22*X28 X23*X29
        DETECTOR(1.5, 0, 0, 1) rec[-66] rec[-65] rec[-64] rec[-12] rec[-11] rec[-10]
        DETECTOR(1.5, 3, 0, 1) rec[-63] rec[-62] rec[-61] rec[-9] rec[-8] rec[-7]
        DETECTOR(3.5, 0, 0, 1) rec[-60] rec[-59] rec[-58] rec[-6] rec[-5] rec[-4]
        DETECTOR(3.5, 3, 0, 1) rec[-57] rec[-56] rec[-55] rec[-3] rec[-2] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP Z0*Z1 Z4*Z5 Z6*Z7 Z10*Z11 Z12*Z13 Z16*Z17 Z18*Z19 Z22*Z23 Z24*Z25 Z28*Z29 Z30*Z31 Z34*Z35
        DETECTOR(10, 0.5, 0, 2) rec[-66] rec[-64] rec[-62] rec[-60] rec[-58] rec[-56] rec[-12] rec[-10] rec[-8] rec[-6] rec[-4] rec[-2]
        DETECTOR(10, 4.5, 0, 2) rec[-65] rec[-63] rec[-61] rec[-59] rec[-57] rec[-55] rec[-11] rec[-9] rec[-7] rec[-5] rec[-3] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP Z1*Z2 Z3*Z4 Z7*Z8 Z9*Z10 Z13*Z14 Z15*Z16 Z19*Z20 Z21*Z22 Z25*Z26 Z27*Z28 Z31*Z32 Z33*Z34
        DETECTOR(10, 1.5, 0, 2) rec[-66] rec[-64] rec[-62] rec[-60] rec[-58] rec[-56] rec[-12] rec[-10] rec[-8] rec[-6] rec[-4] rec[-2]
        DETECTOR(10, 3.5, 0, 2) rec[-65] rec[-63] rec[-61] rec[-59] rec[-57] rec[-55] rec[-11] rec[-9] rec[-7] rec[-5] rec[-3] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP X0*X6 X1*X7 X2*X8 X3*X9 X4*X10 X5*X11 X24*X30 X25*X31 X26*X32 X27*X33 X28*X34 X29*X35
        DETECTOR(0.5, 0, 0, 1) rec[-66] rec[-65] rec[-64] rec[-12] rec[-11] rec[-10]
        DETECTOR(0.5, 3, 0, 1) rec[-63] rec[-62] rec[-61] rec[-9] rec[-8] rec[-7]
        DETECTOR(4.5, 0, 0, 1) rec[-54] rec[-53] rec[-52] rec[-6] rec[-5] rec[-4]
        DETECTOR(4.5, 3, 0, 1) rec[-51] rec[-50] rec[-49] rec[-3] rec[-2] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP X6*X12 X7*X13 X8*X14 X9*X15 X10*X16 X11*X17 X18*X24 X19*X25 X20*X26 X21*X27 X22*X28 X23*X29
        DETECTOR(1.5, 0, 0, 1) rec[-60] rec[-59] rec[-58] rec[-12] rec[-11] rec[-10]
        DETECTOR(1.5, 3, 0, 1) rec[-57] rec[-56] rec[-55] rec[-9] rec[-8] rec[-7]
        DETECTOR(3.5, 0, 0, 1) rec[-54] rec[-53] rec[-52] rec[-6] rec[-5] rec[-4]
        DETECTOR(3.5, 3, 0, 1) rec[-51] rec[-50] rec[-49] rec[-3] rec[-2] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP Z0*Z1 Z2*Z3 Z4*Z5 Z6*Z7 Z8*Z9 Z10*Z11 Z12*Z13 Z14*Z15 Z16*Z17 Z18*Z19 Z20*Z21 Z22*Z23 Z24*Z25 Z26*Z27 Z28*Z29 Z30*Z31 Z32*Z33 Z34*Z35
        DETECTOR(10, 0.5, 0, 2) rec[-66] rec[-64] rec[-62] rec[-18] rec[-15] rec[-12]
        DETECTOR(13, 0.5, 0, 2) rec[-60] rec[-58] rec[-56] rec[-9] rec[-6] rec[-3]
        DETECTOR(10, 4.5, 0, 2) rec[-65] rec[-63] rec[-61] rec[-16] rec[-13] rec[-10]
        DETECTOR(13, 4.5, 0, 2) rec[-59] rec[-57] rec[-55] rec[-7] rec[-4] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP Z1*Z2 Z3*Z4 Z7*Z8 Z9*Z10 Z13*Z14 Z15*Z16 Z19*Z20 Z21*Z22 Z25*Z26 Z27*Z28 Z31*Z32 Z33*Z34
        DETECTOR(10, 1.5, 0, 2) rec[-66] rec[-64] rec[-62] rec[-12] rec[-10] rec[-8]
        DETECTOR(13, 1.5, 0, 2) rec[-60] rec[-58] rec[-56] rec[-6] rec[-4] rec[-2]
        DETECTOR(10, 3.5, 0, 2) rec[-65] rec[-63] rec[-61] rec[-11] rec[-9] rec[-7]
        DETECTOR(13, 3.5, 0, 2) rec[-59] rec[-57] rec[-55] rec[-5] rec[-3] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP X0*X6 X1*X7 X2*X8 X3*X9 X4*X10 X5*X11 X24*X30 X25*X31 X26*X32 X27*X33 X28*X34 X29*X35
        DETECTOR(0.5, 0, 0, 1) rec[-66] rec[-65] rec[-64] rec[-63] rec[-62] rec[-61] rec[-12] rec[-11] rec[-10] rec[-9] rec[-8] rec[-7]
        DETECTOR(4.5, 0, 0, 1) rec[-60] rec[-59] rec[-58] rec[-57] rec[-56] rec[-55] rec[-6] rec[-5] rec[-4] rec[-3] rec[-2] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP X6*X12 X7*X13 X8*X14 X9*X15 X10*X16 X11*X17 X18*X24 X19*X25 X20*X26 X21*X27 X22*X28 X23*X29
        DETECTOR(1.5, 0, 0, 1) rec[-66] rec[-65] rec[-64] rec[-63] rec[-62] rec[-61] rec[-12] rec[-11] rec[-10] rec[-9] rec[-8] rec[-7]
        DETECTOR(3.5, 0, 0, 1) rec[-60] rec[-59] rec[-58] rec[-57] rec[-56] rec[-55] rec[-6] rec[-5] rec[-4] rec[-3] rec[-2] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP Z0*Z1 Z4*Z5 Z6*Z7 Z10*Z11 Z12*Z13 Z16*Z17 Z18*Z19 Z22*Z23 Z24*Z25 Z28*Z29 Z30*Z31 Z34*Z35
        DETECTOR(10, 0.5, 0, 2) rec[-66] rec[-63] rec[-60] rec[-12] rec[-10] rec[-8]
        DETECTOR(13, 0.5, 0, 2) rec[-57] rec[-54] rec[-51] rec[-6] rec[-4] rec[-2]
        DETECTOR(10, 4.5, 0, 2) rec[-64] rec[-61] rec[-58] rec[-11] rec[-9] rec[-7]
        DETECTOR(13, 4.5, 0, 2) rec[-55] rec[-52] rec[-49] rec[-5] rec[-3] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP Z1*Z2 Z3*Z4 Z7*Z8 Z9*Z10 Z13*Z14 Z15*Z16 Z19*Z20 Z21*Z22 Z25*Z26 Z27*Z28 Z31*Z32 Z33*Z34
        DETECTOR(10, 1.5, 0, 2) rec[-60] rec[-58] rec[-56] rec[-12] rec[-10] rec[-8]
        DETECTOR(13, 1.5, 0, 2) rec[-54] rec[-52] rec[-50] rec[-6] rec[-4] rec[-2]
        DETECTOR(10, 3.5, 0, 2) rec[-59] rec[-57] rec[-55] rec[-11] rec[-9] rec[-7]
        DETECTOR(13, 3.5, 0, 2) rec[-53] rec[-51] rec[-49] rec[-5] rec[-3] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP X0*X6 X1*X7 X2*X8 X3*X9 X4*X10 X5*X11 X24*X30 X25*X31 X26*X32 X27*X33 X28*X34 X29*X35
        DETECTOR(0.5, 0, 0, 1) rec[-60] rec[-59] rec[-58] rec[-12] rec[-11] rec[-10]
        DETECTOR(0.5, 3, 0, 1) rec[-57] rec[-56] rec[-55] rec[-9] rec[-8] rec[-7]
        DETECTOR(4.5, 0, 0, 1) rec[-54] rec[-53] rec[-52] rec[-6] rec[-5] rec[-4]
        DETECTOR(4.5, 3, 0, 1) rec[-51] rec[-50] rec[-49] rec[-3] rec[-2] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP X6*X12 X7*X13 X8*X14 X9*X15 X10*X16 X11*X17 X18*X24 X19*X25 X20*X26 X21*X27 X22*X28 X23*X29
        DETECTOR(1.5, 0, 0, 1) rec[-60] rec[-59] rec[-58] rec[-12] rec[-11] rec[-10]
        DETECTOR(1.5, 3, 0, 1) rec[-57] rec[-56] rec[-55] rec[-9] rec[-8] rec[-7]
        DETECTOR(3.5, 0, 0, 1) rec[-54] rec[-53] rec[-52] rec[-6] rec[-5] rec[-4]
        DETECTOR(3.5, 3, 0, 1) rec[-51] rec[-50] rec[-49] rec[-3] rec[-2] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP Z0*Z1 Z4*Z5 Z6*Z7 Z10*Z11 Z12*Z13 Z16*Z17 Z18*Z19 Z22*Z23 Z24*Z25 Z28*Z29 Z30*Z31 Z34*Z35
        DETECTOR(10, 0.5, 0, 2) rec[-60] rec[-58] rec[-56] rec[-12] rec[-10] rec[-8]
        DETECTOR(13, 0.5, 0, 2) rec[-54] rec[-52] rec[-50] rec[-6] rec[-4] rec[-2]
        DETECTOR(10, 4.5, 0, 2) rec[-59] rec[-57] rec[-55] rec[-11] rec[-9] rec[-7]
        DETECTOR(13, 4.5, 0, 2) rec[-53] rec[-51] rec[-49] rec[-5] rec[-3] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP Z1*Z2 Z3*Z4 Z7*Z8 Z9*Z10 Z13*Z14 Z15*Z16 Z19*Z20 Z21*Z22 Z25*Z26 Z27*Z28 Z31*Z32 Z33*Z34
        DETECTOR(10, 1.5, 0, 2) rec[-60] rec[-58] rec[-56] rec[-12] rec[-10] rec[-8]
        DETECTOR(13, 1.5, 0, 2) rec[-54] rec[-52] rec[-50] rec[-6] rec[-4] rec[-2]
        DETECTOR(10, 3.5, 0, 2) rec[-59] rec[-57] rec[-55] rec[-11] rec[-9] rec[-7]
        DETECTOR(13, 3.5, 0, 2) rec[-53] rec[-51] rec[-49] rec[-5] rec[-3] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP X0*X6 X1*X7 X2*X8 X3*X9 X4*X10 X5*X11 X12*X18 X13*X19 X14*X20 X15*X21 X16*X22 X17*X23 X24*X30 X25*X31 X26*X32 X27*X33 X28*X34 X29*X35
        DETECTOR(0.5, 0, 0, 1) rec[-66] rec[-65] rec[-64] rec[-18] rec[-17] rec[-16]
        DETECTOR(0.5, 3, 0, 1) rec[-63] rec[-62] rec[-61] rec[-15] rec[-14] rec[-13]
        DETECTOR(2.5, 0, 0, 1) rec[-216] rec[-215] rec[-214] rec[-213] rec[-212] rec[-211] rec[-12] rec[-11] rec[-10] rec[-9] rec[-8] rec[-7]
        DETECTOR(4.5, 0, 0, 1) rec[-60] rec[-59] rec[-58] rec[-6] rec[-5] rec[-4]
        DETECTOR(4.5, 3, 0, 1) rec[-57] rec[-56] rec[-55] rec[-3] rec[-2] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP X6*X12 X7*X13 X8*X14 X9*X15 X10*X16 X11*X17 X18*X24 X19*X25 X20*X26 X21*X27 X22*X28 X23*X29
        DETECTOR(1.5, 0, 0, 1) rec[-66] rec[-65] rec[-64] rec[-12] rec[-11] rec[-10]
        DETECTOR(1.5, 3, 0, 1) rec[-63] rec[-62] rec[-61] rec[-9] rec[-8] rec[-7]
        DETECTOR(3.5, 0, 0, 1) rec[-60] rec[-59] rec[-58] rec[-6] rec[-5] rec[-4]
        DETECTOR(3.5, 3, 0, 1) rec[-57] rec[-56] rec[-55] rec[-3] rec[-2] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP Z0*Z1 Z4*Z5 Z6*Z7 Z10*Z11 Z12*Z13 Z16*Z17 Z18*Z19 Z22*Z23 Z24*Z25 Z28*Z29 Z30*Z31 Z34*Z35
        DETECTOR(10, 0.5, 0, 2) rec[-66] rec[-64] rec[-62] rec[-60] rec[-58] rec[-56] rec[-12] rec[-10] rec[-8] rec[-6] rec[-4] rec[-2]
        DETECTOR(10, 4.5, 0, 2) rec[-65] rec[-63] rec[-61] rec[-59] rec[-57] rec[-55] rec[-11] rec[-9] rec[-7] rec[-5] rec[-3] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP Z1*Z2 Z3*Z4 Z7*Z8 Z9*Z10 Z13*Z14 Z15*Z16 Z19*Z20 Z21*Z22 Z25*Z26 Z27*Z28 Z31*Z32 Z33*Z34
        DETECTOR(10, 1.5, 0, 2) rec[-66] rec[-64] rec[-62] rec[-60] rec[-58] rec[-56] rec[-12] rec[-10] rec[-8] rec[-6] rec[-4] rec[-2]
        DETECTOR(10, 3.5, 0, 2) rec[-65] rec[-63] rec[-61] rec[-59] rec[-57] rec[-55] rec[-11] rec[-9] rec[-7] rec[-5] rec[-3] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP X0*X6 X1*X7 X2*X8 X3*X9 X4*X10 X5*X11 X24*X30 X25*X31 X26*X32 X27*X33 X28*X34 X29*X35
        DETECTOR(0.5, 0, 0, 1) rec[-66] rec[-65] rec[-64] rec[-12] rec[-11] rec[-10]
        DETECTOR(0.5, 3, 0, 1) rec[-63] rec[-62] rec[-61] rec[-9] rec[-8] rec[-7]
        DETECTOR(4.5, 0, 0, 1) rec[-54] rec[-53] rec[-52] rec[-6] rec[-5] rec[-4]
        DETECTOR(4.5, 3, 0, 1) rec[-51] rec[-50] rec[-49] rec[-3] rec[-2] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP X6*X12 X7*X13 X8*X14 X9*X15 X10*X16 X11*X17 X18*X24 X19*X25 X20*X26 X21*X27 X22*X28 X23*X29
        DETECTOR(1.5, 0, 0, 1) rec[-60] rec[-59] rec[-58] rec[-12] rec[-11] rec[-10]
        DETECTOR(1.5, 3, 0, 1) rec[-57] rec[-56] rec[-55] rec[-9] rec[-8] rec[-7]
        DETECTOR(3.5, 0, 0, 1) rec[-54] rec[-53] rec[-52] rec[-6] rec[-5] rec[-4]
        DETECTOR(3.5, 3, 0, 1) rec[-51] rec[-50] rec[-49] rec[-3] rec[-2] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP Z0*Z1 Z2*Z3 Z4*Z5 Z6*Z7 Z8*Z9 Z10*Z11 Z12*Z13 Z14*Z15 Z16*Z17 Z18*Z19 Z20*Z21 Z22*Z23 Z24*Z25 Z26*Z27 Z28*Z29 Z30*Z31 Z32*Z33 Z34*Z35
        DETECTOR(10, 0.5, 0, 2) rec[-66] rec[-64] rec[-62] rec[-18] rec[-15] rec[-12]
        DETECTOR(13, 0.5, 0, 2) rec[-60] rec[-58] rec[-56] rec[-9] rec[-6] rec[-3]
        DETECTOR(10, 2.5, 0, 2) rec[-221] rec[-218] rec[-215] rec[-212] rec[-209] rec[-206] rec[-17] rec[-14] rec[-11] rec[-8] rec[-5] rec[-2]
        DETECTOR(10, 4.5, 0, 2) rec[-65] rec[-63] rec[-61] rec[-16] rec[-13] rec[-10]
        DETECTOR(13, 4.5, 0, 2) rec[-59] rec[-57] rec[-55] rec[-7] rec[-4] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP Z1*Z2 Z3*Z4 Z7*Z8 Z9*Z10 Z13*Z14 Z15*Z16 Z19*Z20 Z21*Z22 Z25*Z26 Z27*Z28 Z31*Z32 Z33*Z34
        DETECTOR(10, 1.5, 0, 2) rec[-66] rec[-64] rec[-62] rec[-12] rec[-10] rec[-8]
        DETECTOR(13, 1.5, 0, 2) rec[-60] rec[-58] rec[-56] rec[-6] rec[-4] rec[-2]
        DETECTOR(10, 3.5, 0, 2) rec[-65] rec[-63] rec[-61] rec[-11] rec[-9] rec[-7]
        DETECTOR(13, 3.5, 0, 2) rec[-59] rec[-57] rec[-55] rec[-5] rec[-3] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP X0*X6 X1*X7 X2*X8 X3*X9 X4*X10 X5*X11 X24*X30 X25*X31 X26*X32 X27*X33 X28*X34 X29*X35
        DETECTOR(0.5, 0, 0, 1) rec[-66] rec[-65] rec[-64] rec[-63] rec[-62] rec[-61] rec[-12] rec[-11] rec[-10] rec[-9] rec[-8] rec[-7]
        DETECTOR(4.5, 0, 0, 1) rec[-60] rec[-59] rec[-58] rec[-57] rec[-56] rec[-55] rec[-6] rec[-5] rec[-4] rec[-3] rec[-2] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP X6*X12 X7*X13 X8*X14 X9*X15 X10*X16 X11*X17 X18*X24 X19*X25 X20*X26 X21*X27 X22*X28 X23*X29
        DETECTOR(1.5, 0, 0, 1) rec[-66] rec[-65] rec[-64] rec[-63] rec[-62] rec[-61] rec[-12] rec[-11] rec[-10] rec[-9] rec[-8] rec[-7]
        DETECTOR(3.5, 0, 0, 1) rec[-60] rec[-59] rec[-58] rec[-57] rec[-56] rec[-55] rec[-6] rec[-5] rec[-4] rec[-3] rec[-2] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP Z0*Z1 Z4*Z5 Z6*Z7 Z10*Z11 Z12*Z13 Z16*Z17 Z18*Z19 Z22*Z23 Z24*Z25 Z28*Z29 Z30*Z31 Z34*Z35
        DETECTOR(10, 0.5, 0, 2) rec[-66] rec[-63] rec[-60] rec[-12] rec[-10] rec[-8]
        DETECTOR(13, 0.5, 0, 2) rec[-57] rec[-54] rec[-51] rec[-6] rec[-4] rec[-2]
        DETECTOR(10, 4.5, 0, 2) rec[-64] rec[-61] rec[-58] rec[-11] rec[-9] rec[-7]
        DETECTOR(13, 4.5, 0, 2) rec[-55] rec[-52] rec[-49] rec[-5] rec[-3] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP Z1*Z2 Z3*Z4 Z7*Z8 Z9*Z10 Z13*Z14 Z15*Z16 Z19*Z20 Z21*Z22 Z25*Z26 Z27*Z28 Z31*Z32 Z33*Z34
        DETECTOR(10, 1.5, 0, 2) rec[-60] rec[-58] rec[-56] rec[-12] rec[-10] rec[-8]
        DETECTOR(13, 1.5, 0, 2) rec[-54] rec[-52] rec[-50] rec[-6] rec[-4] rec[-2]
        DETECTOR(10, 3.5, 0, 2) rec[-59] rec[-57] rec[-55] rec[-11] rec[-9] rec[-7]
        DETECTOR(13, 3.5, 0, 2) rec[-53] rec[-51] rec[-49] rec[-5] rec[-3] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP X0*X6 X1*X7 X2*X8 X3*X9 X4*X10 X5*X11 X24*X30 X25*X31 X26*X32 X27*X33 X28*X34 X29*X35
        DETECTOR(0.5, 0, 0, 1) rec[-60] rec[-59] rec[-58] rec[-12] rec[-11] rec[-10]
        DETECTOR(0.5, 3, 0, 1) rec[-57] rec[-56] rec[-55] rec[-9] rec[-8] rec[-7]
        DETECTOR(4.5, 0, 0, 1) rec[-54] rec[-53] rec[-52] rec[-6] rec[-5] rec[-4]
        DETECTOR(4.5, 3, 0, 1) rec[-51] rec[-50] rec[-49] rec[-3] rec[-2] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP X6*X12 X7*X13 X8*X14 X9*X15 X10*X16 X11*X17 X18*X24 X19*X25 X20*X26 X21*X27 X22*X28 X23*X29
        DETECTOR(1.5, 0, 0, 1) rec[-60] rec[-59] rec[-58] rec[-12] rec[-11] rec[-10]
        DETECTOR(1.5, 3, 0, 1) rec[-57] rec[-56] rec[-55] rec[-9] rec[-8] rec[-7]
        DETECTOR(3.5, 0, 0, 1) rec[-54] rec[-53] rec[-52] rec[-6] rec[-5] rec[-4]
        DETECTOR(3.5, 3, 0, 1) rec[-51] rec[-50] rec[-49] rec[-3] rec[-2] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP Z0*Z1 Z4*Z5 Z6*Z7 Z10*Z11 Z12*Z13 Z16*Z17 Z18*Z19 Z22*Z23 Z24*Z25 Z28*Z29 Z30*Z31 Z34*Z35
        DETECTOR(10, 0.5, 0, 2) rec[-60] rec[-58] rec[-56] rec[-12] rec[-10] rec[-8]
        DETECTOR(13, 0.5, 0, 2) rec[-54] rec[-52] rec[-50] rec[-6] rec[-4] rec[-2]
        DETECTOR(10, 4.5, 0, 2) rec[-59] rec[-57] rec[-55] rec[-11] rec[-9] rec[-7]
        DETECTOR(13, 4.5, 0, 2) rec[-53] rec[-51] rec[-49] rec[-5] rec[-3] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP Z1*Z2 Z3*Z4 Z7*Z8 Z9*Z10 Z13*Z14 Z15*Z16 Z19*Z20 Z21*Z22 Z25*Z26 Z27*Z28 Z31*Z32 Z33*Z34
        DETECTOR(10, 1.5, 0, 2) rec[-60] rec[-58] rec[-56] rec[-12] rec[-10] rec[-8]
        DETECTOR(13, 1.5, 0, 2) rec[-54] rec[-52] rec[-50] rec[-6] rec[-4] rec[-2]
        DETECTOR(10, 3.5, 0, 2) rec[-59] rec[-57] rec[-55] rec[-11] rec[-9] rec[-7]
        DETECTOR(13, 3.5, 0, 2) rec[-53] rec[-51] rec[-49] rec[-5] rec[-3] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MX 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35
        OBSERVABLE_INCLUDE(0) rec[-36] rec[-35] rec[-34] rec[-33] rec[-32] rec[-31]
        DETECTOR(0.5, 0, 0, 1) rec[-84] rec[-83] rec[-82] rec[-36] rec[-35] rec[-34] rec[-30] rec[-29] rec[-28]
        DETECTOR(0.5, 3, 0, 1) rec[-81] rec[-80] rec[-79] rec[-33] rec[-32] rec[-31] rec[-27] rec[-26] rec[-25]
        DETECTOR(1.5, 0, 0, 1) rec[-72] rec[-71] rec[-70] rec[-30] rec[-29] rec[-28] rec[-24] rec[-23] rec[-22]
        DETECTOR(1.5, 3, 0, 1) rec[-69] rec[-68] rec[-67] rec[-27] rec[-26] rec[-25] rec[-21] rec[-20] rec[-19]
        DETECTOR(2.5, 0, 0, 1) rec[-234] rec[-233] rec[-232] rec[-231] rec[-230] rec[-229] rec[-24] rec[-23] rec[-22] rec[-21] rec[-20] rec[-19] rec[-18] rec[-17] rec[-16] rec[-15] rec[-14] rec[-13]
        DETECTOR(3.5, 0, 0, 1) rec[-66] rec[-65] rec[-64] rec[-18] rec[-17] rec[-16] rec[-12] rec[-11] rec[-10]
        DETECTOR(3.5, 3, 0, 1) rec[-63] rec[-62] rec[-61] rec[-15] rec[-14] rec[-13] rec[-9] rec[-8] rec[-7]
        DETECTOR(4.5, 0, 0, 1) rec[-78] rec[-77] rec[-76] rec[-12] rec[-11] rec[-10] rec[-6] rec[-5] rec[-4]
        DETECTOR(4.5, 3, 0, 1) rec[-75] rec[-74] rec[-73] rec[-9] rec[-8] rec[-7] rec[-3] rec[-2] rec[-1]
    """)
