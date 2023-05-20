import itertools

import pytest

import gen
from baconshor._bacon_shor_lattice_surgery import \
    make_bacon_shor_xx_lattice_surgery_circuit


@pytest.mark.parametrize('width,height,basis,rounds', itertools.product(
    [4, 6],
    [6, 12],
    ['X', 'Z'],
    [1, 5, 6],
))
def test_make_bacon_shor_xx_lattice_surgery_circuit(width: int, height: int, basis: str, rounds: int):
    circuit = make_bacon_shor_xx_lattice_surgery_circuit(
        width=width,
        height=height,
        basis=basis,
        rounds=rounds,
    )
    circuit = gen.NoiseModel.uniform_depolarizing(1e-3).noisy_circuit(circuit)
    circuit.detector_error_model()

    expected_determined = circuit.num_detectors + circuit.num_observables
    assert gen.count_determined_measurements_in_circuit(circuit) == expected_determined

    assert circuit.num_ticks == (rounds + 2) * 4 + 1

    expected_distance = min(width // 2, rounds) if basis == 'X' else height // 2
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
