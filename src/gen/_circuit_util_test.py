import stim

import gen
from gen._circuit_util import make_code_capacity_circuit_for_stabilizer_code, \
    make_phenomenological_circuit_for_stabilizer_code, gates_used_by_circuit


def test_make_phenomenological_circuit_for_stabilizer_code():
    patch = gen.Patch([
        gen.Tile(
            bases='Z',
            ordered_data_qubits=[0, 1, 1j, 1 + 1j],
            measurement_qubit=0.5 + 0.5j,
        ),
        gen.Tile(
            bases='X',
            ordered_data_qubits=[0, 1],
            measurement_qubit=0.5,
        ),
        gen.Tile(
            bases='X',
            ordered_data_qubits=[0 + 1j, 1 + 1j],
            measurement_qubit=0.5 + 1j,
        ),
    ])
    obs_x=gen.PauliString({0: 'X', 1j: 'X'})
    obs_z=gen.PauliString({0: 'Z', 1: 'Z'})

    assert make_phenomenological_circuit_for_stabilizer_code(
        patch=patch,
        noise=gen.NoiseRule(flip_result=0.125, after={'DEPOLARIZE1': 0.25}),
        obs_x=obs_x,
        obs_z=obs_z,
        basis='X',
        rounds=100,
    ) == stim.Circuit("""
        QUBIT_COORDS(0, 0) 0
        QUBIT_COORDS(0, 1) 1
        QUBIT_COORDS(1, 0) 2
        QUBIT_COORDS(1, 1) 3
        MPP X0*X1
        OBSERVABLE_INCLUDE(0) rec[-1]
        MPP X0*X2 Z0*Z1*Z2*Z3 X1*X3
        TICK
        REPEAT 100 {
            MPP(0.125) X0*X2 Z0*Z1*Z2*Z3 X1*X3
            DETECTOR(0.5, 0, 0) rec[-6] rec[-3]
            DETECTOR(0.5, 0.5, 0) rec[-5] rec[-2]
            DETECTOR(0.5, 1, 0) rec[-4] rec[-1]
            SHIFT_COORDS(0, 0, 1)
            DEPOLARIZE1(0.25) 0 1 2 3
        }
        MPP X0*X2 Z0*Z1*Z2*Z3 X1*X3
        DETECTOR(0.5, 0, 0) rec[-6] rec[-3]
        DETECTOR(0.5, 0.5, 0) rec[-5] rec[-2]
        DETECTOR(0.5, 1, 0) rec[-4] rec[-1]
        MPP X0*X1
        OBSERVABLE_INCLUDE(0) rec[-1]
    """)

    assert make_phenomenological_circuit_for_stabilizer_code(
        patch=patch,
        noise=gen.NoiseRule(flip_result=0.125, after={'DEPOLARIZE1': 0.25}),
        obs_x=obs_x,
        obs_z=obs_z,
        basis='Z',
        rounds=100,
    ) == stim.Circuit("""
        QUBIT_COORDS(0, 0) 0
        QUBIT_COORDS(0, 1) 1
        QUBIT_COORDS(1, 0) 2
        QUBIT_COORDS(1, 1) 3
        MPP Z0*Z2
        OBSERVABLE_INCLUDE(0) rec[-1]
        MPP X0*X2 Z0*Z1*Z2*Z3 X1*X3
        TICK
        REPEAT 100 {
            MPP(0.125) X0*X2 Z0*Z1*Z2*Z3 X1*X3
            DETECTOR(0.5, 0, 0) rec[-6] rec[-3]
            DETECTOR(0.5, 0.5, 0) rec[-5] rec[-2]
            DETECTOR(0.5, 1, 0) rec[-4] rec[-1]
            SHIFT_COORDS(0, 0, 1)
            DEPOLARIZE1(0.25) 0 1 2 3
        }
        MPP X0*X2 Z0*Z1*Z2*Z3 X1*X3
        DETECTOR(0.5, 0, 0) rec[-6] rec[-3]
        DETECTOR(0.5, 0.5, 0) rec[-5] rec[-2]
        DETECTOR(0.5, 1, 0) rec[-4] rec[-1]
        MPP Z0*Z2
        OBSERVABLE_INCLUDE(0) rec[-1]
    """)

    assert make_phenomenological_circuit_for_stabilizer_code(
        patch=patch,
        noise=gen.NoiseRule(flip_result=0.125, after={'DEPOLARIZE1': 0.25}),
        obs_x=obs_x,
        obs_z=obs_z,
        basis='XZ',
        rounds=100,
    ) == stim.Circuit("""
        QUBIT_COORDS(0, 0) 0
        QUBIT_COORDS(0, 1) 1
        QUBIT_COORDS(1, 0) 2
        QUBIT_COORDS(1, 1) 3
        QUBIT_COORDS(2, 1) 4
        MPP X0*X1*X4
        OBSERVABLE_INCLUDE(0) rec[-1]
        MPP Z0*Z2*Z4
        OBSERVABLE_INCLUDE(1) rec[-1]
        MPP X0*X2 Z0*Z1*Z2*Z3 X1*X3
        TICK
        REPEAT 100 {
            MPP(0.125) X0*X2 Z0*Z1*Z2*Z3 X1*X3
            DETECTOR(0.5, 0, 0) rec[-6] rec[-3]
            DETECTOR(0.5, 0.5, 0) rec[-5] rec[-2]
            DETECTOR(0.5, 1, 0) rec[-4] rec[-1]
            SHIFT_COORDS(0, 0, 1)
            DEPOLARIZE1(0.25) 0 1 2 3
        }
        MPP X0*X2 Z0*Z1*Z2*Z3 X1*X3
        DETECTOR(0.5, 0, 0) rec[-6] rec[-3]
        DETECTOR(0.5, 0.5, 0) rec[-5] rec[-2]
        DETECTOR(0.5, 1, 0) rec[-4] rec[-1]
        MPP X0*X1*X4
        OBSERVABLE_INCLUDE(0) rec[-1]
        MPP Z0*Z2*Z4
        OBSERVABLE_INCLUDE(1) rec[-1]
    """)


def test_make_code_capacity_circuit_for_stabilizer_code():
    patch = gen.Patch([
        gen.Tile(
            bases='Z',
            ordered_data_qubits=[0, 1, 1j, 1 + 1j],
            measurement_qubit=0.5 + 0.5j,
        ),
        gen.Tile(
            bases='X',
            ordered_data_qubits=[0, 1],
            measurement_qubit=0.5,
        ),
        gen.Tile(
            bases='X',
            ordered_data_qubits=[0 + 1j, 1 + 1j],
            measurement_qubit=0.5 + 1j,
        ),
    ])
    obs_x=gen.PauliString({0: 'X', 1j: 'X'})
    obs_z=gen.PauliString({0: 'Z', 1: 'Z'})

    assert make_code_capacity_circuit_for_stabilizer_code(
        patch=patch,
        noise=gen.NoiseRule(after={'DEPOLARIZE1': 0.25}),
        obs_x=obs_x,
        obs_z=obs_z,
        basis='X',
    ) == stim.Circuit("""
        QUBIT_COORDS(0, 0) 0
        QUBIT_COORDS(0, 1) 1
        QUBIT_COORDS(1, 0) 2
        QUBIT_COORDS(1, 1) 3
        MPP X0*X1
        OBSERVABLE_INCLUDE(0) rec[-1]
        MPP X0*X2 Z0*Z1*Z2*Z3 X1*X3
        TICK
        DEPOLARIZE1(0.25) 0 1 2 3
        TICK
        MPP X0*X2 Z0*Z1*Z2*Z3 X1*X3
        DETECTOR(0.5, 0, 0) rec[-6] rec[-3]
        DETECTOR(0.5, 0.5, 0) rec[-5] rec[-2]
        DETECTOR(0.5, 1, 0) rec[-4] rec[-1]
        MPP X0*X1
        OBSERVABLE_INCLUDE(0) rec[-1]
    """)

    assert make_code_capacity_circuit_for_stabilizer_code(
        patch=patch,
        noise=gen.NoiseRule(after={'DEPOLARIZE1': 0.25}),
        obs_x=obs_x,
        obs_z=obs_z,
        basis='Z',
    ) == stim.Circuit("""
        QUBIT_COORDS(0, 0) 0
        QUBIT_COORDS(0, 1) 1
        QUBIT_COORDS(1, 0) 2
        QUBIT_COORDS(1, 1) 3
        MPP Z0*Z2
        OBSERVABLE_INCLUDE(0) rec[-1]
        MPP X0*X2 Z0*Z1*Z2*Z3 X1*X3
        TICK
        DEPOLARIZE1(0.25) 0 1 2 3
        TICK
        MPP X0*X2 Z0*Z1*Z2*Z3 X1*X3
        DETECTOR(0.5, 0, 0) rec[-6] rec[-3]
        DETECTOR(0.5, 0.5, 0) rec[-5] rec[-2]
        DETECTOR(0.5, 1, 0) rec[-4] rec[-1]
        MPP Z0*Z2
        OBSERVABLE_INCLUDE(0) rec[-1]
    """)

    assert make_code_capacity_circuit_for_stabilizer_code(
        patch=patch,
        noise=gen.NoiseRule(after={'DEPOLARIZE1': 0.25}),
        obs_x=obs_x,
        obs_z=obs_z,
        basis='XZ',
    ) == stim.Circuit("""
        QUBIT_COORDS(0, 0) 0
        QUBIT_COORDS(0, 1) 1
        QUBIT_COORDS(1, 0) 2
        QUBIT_COORDS(1, 1) 3
        QUBIT_COORDS(2, 1) 4
        MPP X0*X1*X4
        OBSERVABLE_INCLUDE(0) rec[-1]
        MPP Z0*Z2*Z4
        OBSERVABLE_INCLUDE(1) rec[-1]
        MPP X0*X2 Z0*Z1*Z2*Z3 X1*X3
        TICK
        DEPOLARIZE1(0.25) 0 1 2 3
        TICK
        MPP X0*X2 Z0*Z1*Z2*Z3 X1*X3
        DETECTOR(0.5, 0, 0) rec[-6] rec[-3]
        DETECTOR(0.5, 0.5, 0) rec[-5] rec[-2]
        DETECTOR(0.5, 1, 0) rec[-4] rec[-1]
        MPP X0*X1*X4
        OBSERVABLE_INCLUDE(0) rec[-1]
        MPP Z0*Z2*Z4
        OBSERVABLE_INCLUDE(1) rec[-1]
    """)


def test_gates_used_by_circuit():
    assert gates_used_by_circuit(stim.Circuit("""
        H 0
        TICK
        CX 0 1
    """)) == {'H', 'TICK', 'CX'}

    assert gates_used_by_circuit(stim.Circuit("""
        S 0
        XCZ 0 1
    """)) == {'S', 'XCZ'}

    assert gates_used_by_circuit(stim.Circuit("""
        MPP X0*X1 Z2*Z3*Z4 Y0*Z1
    """)) == {'MXX', 'MZZZ', 'MYZ'}

    assert gates_used_by_circuit(stim.Circuit("""
        CX rec[-1] 1
    """)) == {'feedback'}

    assert gates_used_by_circuit(stim.Circuit("""
        CX sweep[1] 1
    """)) == {'sweep'}

    assert gates_used_by_circuit(stim.Circuit("""
        CX rec[-1] 1 0 1
    """)) == {'feedback', 'CX'}
