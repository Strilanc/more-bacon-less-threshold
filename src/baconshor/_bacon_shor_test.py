import itertools

import pytest
import stim

import gen
from baconshor._bacon_shor import make_bacon_shor_patch, \
    make_bacon_shor_round, make_bacon_shor_circuit


def test_patch():
    patch = make_bacon_shor_patch(
        width=2,
        height=3,
    ).patch
    assert patch == gen.Patch(tiles=[
        gen.Tile(
            ordered_data_qubits=(0j, 1j),
            measurement_qubit=0.5j,
            bases='Z',
        ),
        gen.Tile(
            ordered_data_qubits=(1j, 2j),
            measurement_qubit=1.5j,
            bases='Z',
        ),
        gen.Tile(
            ordered_data_qubits=((1+0j), (1+1j)),
            measurement_qubit=(1+0.5j),
            bases='Z',
        ),
        gen.Tile(
            ordered_data_qubits=((1+1j), (1+2j)),
            measurement_qubit=(1+1.5j),
            bases='Z',
        ),
        gen.Tile(
            ordered_data_qubits=(0j, (1+0j)),
            measurement_qubit=(0.5+0j),
            bases='X',
        ),
        gen.Tile(
            ordered_data_qubits=(1j, (1+1j)),
            measurement_qubit=(0.5+1j),
            bases='X',
        ),
        gen.Tile(
            ordered_data_qubits=(2j, (1+2j)),
            measurement_qubit=(0.5+2j),
            bases='X',
        ),
    ])


def test_code_obs():
    code = make_bacon_shor_patch(
        width=4,
        height=6,
    )
    assert code.obs_x == gen.PauliString({0j: 'X', 1j: 'X', 2j: 'X', 3j: 'X', 4j: 'X', 5j: 'X'})
    assert code.obs_z == gen.PauliString({0j: 'Z', (1+0j): 'Z', (2+0j): 'Z', (3+0j): 'Z'})


@pytest.mark.parametrize('width,height,basis,init,end', itertools.product(
    [4, 6],
    [6, 12],
    ['X', 'Z'],
    [False, True],
    [False, True],
))
def test_round(width: int, height: int, basis: str, init: bool, end: bool):
    make_bacon_shor_round(
        width=width,
        height=height,
        basis=basis,
        init=init,
        end=end,
    ).verify()


@pytest.mark.parametrize('width,height,basis,rounds', itertools.product(
    [4, 6],
    [6, 12],
    ['X', 'Z'],
    [1, 5, 6],
))
def test_make_circuit(width: int, height: int, basis: str, rounds: int):
    chunks = make_bacon_shor_circuit(
        width=width,
        height=height,
        basis=basis,
        rounds=rounds,
    )
    circuit = gen.generate_noisy_circuit_from_chunks(
        chunks=chunks,
        noise=gen.NoiseModel.uniform_depolarizing(1e-3),
        allow_magic_chunks=True,
        convert_to_cz=False,
    )

    expected_determined = circuit.num_detectors + circuit.num_observables
    assert gen.count_determined_measurements_in_circuit(circuit) == expected_determined

    assert circuit.num_ticks == rounds * 4 + 1

    expected_distance = width // 2 if basis == 'X' else height // 2
    actual_distance = len(circuit.shortest_graphlike_error())
    assert actual_distance == expected_distance

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
    rounds = 100
    chunks = make_bacon_shor_circuit(
        width=width,
        height=height,
        basis=basis,
        rounds=rounds,
    )
    circuit = gen.generate_noisy_circuit_from_chunks(
        chunks=chunks,
        noise=gen.NoiseModel.uniform_depolarizing(2**-6),
        allow_magic_chunks=True,
        convert_to_cz=False,
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
        Z_ERROR(0.015625) 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35
        TICK
        MPP(0.015625) X0*X6 X1*X7 X2*X8 X3*X9 X4*X10 X5*X11 X12*X18 X13*X19 X14*X20 X15*X21 X16*X22 X17*X23 X24*X30 X25*X31 X26*X32 X27*X33 X28*X34 X29*X35
        DEPOLARIZE2(0.015625) 0 6 1 7 2 8 3 9 4 10 5 11 12 18 13 19 14 20 15 21 16 22 17 23 24 30 25 31 26 32 27 33 28 34 29 35
        TICK
        MPP(0.015625) X6*X12 X7*X13 X8*X14 X9*X15 X10*X16 X11*X17 X18*X24 X19*X25 X20*X26 X21*X27 X22*X28 X23*X29
        DEPOLARIZE2(0.015625) 6 12 7 13 8 14 9 15 10 16 11 17 18 24 19 25 20 26 21 27 22 28 23 29
        DEPOLARIZE1(0.015625) 0 1 2 3 4 5 30 31 32 33 34 35
        TICK
        MPP(0.015625) Z0*Z1 Z2*Z3 Z4*Z5 Z6*Z7 Z8*Z9 Z10*Z11 Z12*Z13 Z14*Z15 Z16*Z17 Z18*Z19 Z20*Z21 Z22*Z23 Z24*Z25 Z26*Z27 Z28*Z29 Z30*Z31 Z32*Z33 Z34*Z35
        DEPOLARIZE2(0.015625) 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35
        TICK
        MPP(0.015625) Z1*Z2 Z3*Z4 Z7*Z8 Z9*Z10 Z13*Z14 Z15*Z16 Z19*Z20 Z21*Z22 Z25*Z26 Z27*Z28 Z31*Z32 Z33*Z34
        DETECTOR(0.5, 0, 0) rec[-60]
        DETECTOR(0.5, 1, 0) rec[-59]
        DETECTOR(0.5, 2, 0) rec[-58]
        DETECTOR(0.5, 3, 0) rec[-57]
        DETECTOR(0.5, 4, 0) rec[-56]
        DETECTOR(0.5, 5, 0) rec[-55]
        DETECTOR(1.5, 0, 0) rec[-42]
        DETECTOR(1.5, 1, 0) rec[-41]
        DETECTOR(1.5, 2, 0) rec[-40]
        DETECTOR(1.5, 3, 0) rec[-39]
        DETECTOR(1.5, 4, 0) rec[-38]
        DETECTOR(1.5, 5, 0) rec[-37]
        DETECTOR(2.5, 0, 0) rec[-54]
        DETECTOR(2.5, 1, 0) rec[-53]
        DETECTOR(2.5, 2, 0) rec[-52]
        DETECTOR(2.5, 3, 0) rec[-51]
        DETECTOR(2.5, 4, 0) rec[-50]
        DETECTOR(2.5, 5, 0) rec[-49]
        DETECTOR(3.5, 0, 0) rec[-36]
        DETECTOR(3.5, 1, 0) rec[-35]
        DETECTOR(3.5, 2, 0) rec[-34]
        DETECTOR(3.5, 3, 0) rec[-33]
        DETECTOR(3.5, 4, 0) rec[-32]
        DETECTOR(3.5, 5, 0) rec[-31]
        DETECTOR(4.5, 0, 0) rec[-48]
        DETECTOR(4.5, 1, 0) rec[-47]
        DETECTOR(4.5, 2, 0) rec[-46]
        DETECTOR(4.5, 3, 0) rec[-45]
        DETECTOR(4.5, 4, 0) rec[-44]
        DETECTOR(4.5, 5, 0) rec[-43]
        SHIFT_COORDS(0, 0, 1)
        DEPOLARIZE2(0.015625) 1 2 3 4 7 8 9 10 13 14 15 16 19 20 21 22 25 26 27 28 31 32 33 34
        DEPOLARIZE1(0.015625) 0 5 6 11 12 17 18 23 24 29 30 35
        TICK
        REPEAT 98 {
            MPP(0.015625) X0*X6 X1*X7 X2*X8 X3*X9 X4*X10 X5*X11 X12*X18 X13*X19 X14*X20 X15*X21 X16*X22 X17*X23 X24*X30 X25*X31 X26*X32 X27*X33 X28*X34 X29*X35
            DEPOLARIZE2(0.015625) 0 6 1 7 2 8 3 9 4 10 5 11 12 18 13 19 14 20 15 21 16 22 17 23 24 30 25 31 26 32 27 33 28 34 29 35
            TICK
            MPP(0.015625) X6*X12 X7*X13 X8*X14 X9*X15 X10*X16 X11*X17 X18*X24 X19*X25 X20*X26 X21*X27 X22*X28 X23*X29
            DEPOLARIZE2(0.015625) 6 12 7 13 8 14 9 15 10 16 11 17 18 24 19 25 20 26 21 27 22 28 23 29
            DEPOLARIZE1(0.015625) 0 1 2 3 4 5 30 31 32 33 34 35
            TICK
            MPP(0.015625) Z0*Z1 Z2*Z3 Z4*Z5 Z6*Z7 Z8*Z9 Z10*Z11 Z12*Z13 Z14*Z15 Z16*Z17 Z18*Z19 Z20*Z21 Z22*Z23 Z24*Z25 Z26*Z27 Z28*Z29 Z30*Z31 Z32*Z33 Z34*Z35
            DEPOLARIZE2(0.015625) 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35
            TICK
            MPP(0.015625) Z1*Z2 Z3*Z4 Z7*Z8 Z9*Z10 Z13*Z14 Z15*Z16 Z19*Z20 Z21*Z22 Z25*Z26 Z27*Z28 Z31*Z32 Z33*Z34
            DETECTOR(0.5, 0, 0) rec[-120] rec[-119] rec[-118] rec[-117] rec[-116] rec[-115] rec[-60] rec[-59] rec[-58] rec[-57] rec[-56] rec[-55]
            DETECTOR(1.5, 0, 0) rec[-102] rec[-101] rec[-100] rec[-99] rec[-98] rec[-97] rec[-42] rec[-41] rec[-40] rec[-39] rec[-38] rec[-37]
            DETECTOR(2.5, 0, 0) rec[-114] rec[-113] rec[-112] rec[-111] rec[-110] rec[-109] rec[-54] rec[-53] rec[-52] rec[-51] rec[-50] rec[-49]
            DETECTOR(3.5, 0, 0) rec[-96] rec[-95] rec[-94] rec[-93] rec[-92] rec[-91] rec[-36] rec[-35] rec[-34] rec[-33] rec[-32] rec[-31]
            DETECTOR(4.5, 0, 0) rec[-108] rec[-107] rec[-106] rec[-105] rec[-104] rec[-103] rec[-48] rec[-47] rec[-46] rec[-45] rec[-44] rec[-43]
            DETECTOR(0, 0.5, 0) rec[-90] rec[-87] rec[-84] rec[-81] rec[-78] rec[-75] rec[-30] rec[-27] rec[-24] rec[-21] rec[-18] rec[-15]
            DETECTOR(0, 1.5, 0) rec[-72] rec[-70] rec[-68] rec[-66] rec[-64] rec[-62] rec[-12] rec[-10] rec[-8] rec[-6] rec[-4] rec[-2]
            DETECTOR(0, 2.5, 0) rec[-89] rec[-86] rec[-83] rec[-80] rec[-77] rec[-74] rec[-29] rec[-26] rec[-23] rec[-20] rec[-17] rec[-14]
            DETECTOR(0, 3.5, 0) rec[-71] rec[-69] rec[-67] rec[-65] rec[-63] rec[-61] rec[-11] rec[-9] rec[-7] rec[-5] rec[-3] rec[-1]
            DETECTOR(0, 4.5, 0) rec[-88] rec[-85] rec[-82] rec[-79] rec[-76] rec[-73] rec[-28] rec[-25] rec[-22] rec[-19] rec[-16] rec[-13]
            SHIFT_COORDS(0, 0, 1)
            DEPOLARIZE2(0.015625) 1 2 3 4 7 8 9 10 13 14 15 16 19 20 21 22 25 26 27 28 31 32 33 34
            DEPOLARIZE1(0.015625) 0 5 6 11 12 17 18 23 24 29 30 35
            TICK
        }
        MPP(0.015625) X0*X6 X1*X7 X2*X8 X3*X9 X4*X10 X5*X11 X12*X18 X13*X19 X14*X20 X15*X21 X16*X22 X17*X23 X24*X30 X25*X31 X26*X32 X27*X33 X28*X34 X29*X35
        DEPOLARIZE2(0.015625) 0 6 1 7 2 8 3 9 4 10 5 11 12 18 13 19 14 20 15 21 16 22 17 23 24 30 25 31 26 32 27 33 28 34 29 35
        TICK
        MPP(0.015625) X6*X12 X7*X13 X8*X14 X9*X15 X10*X16 X11*X17 X18*X24 X19*X25 X20*X26 X21*X27 X22*X28 X23*X29
        DEPOLARIZE2(0.015625) 6 12 7 13 8 14 9 15 10 16 11 17 18 24 19 25 20 26 21 27 22 28 23 29
        DEPOLARIZE1(0.015625) 0 1 2 3 4 5 30 31 32 33 34 35
        TICK
        MPP(0.015625) Z0*Z1 Z2*Z3 Z4*Z5 Z6*Z7 Z8*Z9 Z10*Z11 Z12*Z13 Z14*Z15 Z16*Z17 Z18*Z19 Z20*Z21 Z22*Z23 Z24*Z25 Z26*Z27 Z28*Z29 Z30*Z31 Z32*Z33 Z34*Z35
        DEPOLARIZE2(0.015625) 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35
        TICK
        MPP(0.015625) Z1*Z2 Z3*Z4 Z7*Z8 Z9*Z10 Z13*Z14 Z15*Z16 Z19*Z20 Z21*Z22 Z25*Z26 Z27*Z28 Z31*Z32 Z33*Z34
        DEPOLARIZE2(0.015625) 1 2 3 4 7 8 9 10 13 14 15 16 19 20 21 22 25 26 27 28 31 32 33 34
        DEPOLARIZE1(0.015625) 0 5 6 11 12 17 18 23 24 29 30 35
        TICK
        MX(0.015625) 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35
        DETECTOR(0.5, 0, 0) rec[-156] rec[-155] rec[-154] rec[-153] rec[-152] rec[-151] rec[-96] rec[-95] rec[-94] rec[-93] rec[-92] rec[-91]
        DETECTOR(0.5, 0, 0) rec[-96] rec[-95] rec[-94] rec[-93] rec[-92] rec[-91] rec[-36] rec[-35] rec[-34] rec[-33] rec[-32] rec[-31] rec[-30] rec[-29] rec[-28] rec[-27] rec[-26] rec[-25]
        DETECTOR(1.5, 0, 0) rec[-138] rec[-137] rec[-136] rec[-135] rec[-134] rec[-133] rec[-78] rec[-77] rec[-76] rec[-75] rec[-74] rec[-73]
        DETECTOR(1.5, 0, 0) rec[-78] rec[-77] rec[-76] rec[-75] rec[-74] rec[-73] rec[-30] rec[-29] rec[-28] rec[-27] rec[-26] rec[-25] rec[-24] rec[-23] rec[-22] rec[-21] rec[-20] rec[-19]
        DETECTOR(2.5, 0, 0) rec[-150] rec[-149] rec[-148] rec[-147] rec[-146] rec[-145] rec[-90] rec[-89] rec[-88] rec[-87] rec[-86] rec[-85]
        DETECTOR(2.5, 0, 0) rec[-90] rec[-89] rec[-88] rec[-87] rec[-86] rec[-85] rec[-24] rec[-23] rec[-22] rec[-21] rec[-20] rec[-19] rec[-18] rec[-17] rec[-16] rec[-15] rec[-14] rec[-13]
        DETECTOR(3.5, 0, 0) rec[-132] rec[-131] rec[-130] rec[-129] rec[-128] rec[-127] rec[-72] rec[-71] rec[-70] rec[-69] rec[-68] rec[-67]
        DETECTOR(3.5, 0, 0) rec[-72] rec[-71] rec[-70] rec[-69] rec[-68] rec[-67] rec[-18] rec[-17] rec[-16] rec[-15] rec[-14] rec[-13] rec[-12] rec[-11] rec[-10] rec[-9] rec[-8] rec[-7]
        DETECTOR(4.5, 0, 0) rec[-144] rec[-143] rec[-142] rec[-141] rec[-140] rec[-139] rec[-84] rec[-83] rec[-82] rec[-81] rec[-80] rec[-79]
        DETECTOR(4.5, 0, 0) rec[-84] rec[-83] rec[-82] rec[-81] rec[-80] rec[-79] rec[-12] rec[-11] rec[-10] rec[-9] rec[-8] rec[-7] rec[-6] rec[-5] rec[-4] rec[-3] rec[-2] rec[-1]
        DETECTOR(0, 0.5, 0) rec[-126] rec[-123] rec[-120] rec[-117] rec[-114] rec[-111] rec[-66] rec[-63] rec[-60] rec[-57] rec[-54] rec[-51]
        DETECTOR(0, 1.5, 0) rec[-108] rec[-106] rec[-104] rec[-102] rec[-100] rec[-98] rec[-48] rec[-46] rec[-44] rec[-42] rec[-40] rec[-38]
        DETECTOR(0, 2.5, 0) rec[-125] rec[-122] rec[-119] rec[-116] rec[-113] rec[-110] rec[-65] rec[-62] rec[-59] rec[-56] rec[-53] rec[-50]
        DETECTOR(0, 3.5, 0) rec[-107] rec[-105] rec[-103] rec[-101] rec[-99] rec[-97] rec[-47] rec[-45] rec[-43] rec[-41] rec[-39] rec[-37]
        DETECTOR(0, 4.5, 0) rec[-124] rec[-121] rec[-118] rec[-115] rec[-112] rec[-109] rec[-64] rec[-61] rec[-58] rec[-55] rec[-52] rec[-49]
        OBSERVABLE_INCLUDE(0) rec[-36] rec[-35] rec[-34] rec[-33] rec[-32] rec[-31]
        SHIFT_COORDS(0, 0, 1)
        DEPOLARIZE1(0.015625) 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35
    """)
