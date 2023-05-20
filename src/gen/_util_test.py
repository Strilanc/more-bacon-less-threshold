import stim

from gen._util import estimate_qubit_count_during_postselection, \
    count_determined_measurements_in_circuit


def test_estimate_qubit_count_during_postselection():
    assert estimate_qubit_count_during_postselection(stim.Circuit("""
        QUBIT_COORDS(0, 0) 100
        H 55
        M 55
    """)) == 0

    assert estimate_qubit_count_during_postselection(stim.Circuit("""
        QUBIT_COORDS(0, 0) 100
        H 55
        M 55
        DETECTOR(0, 0, 0, 999) rec[-1]
    """)) == 1

    assert estimate_qubit_count_during_postselection(stim.Circuit("""
        QUBIT_COORDS(0, 0) 100
        H 55 56
        M 55
        DETECTOR(0, 0, 0, 999) rec[-1]
    """)) == 2

    assert estimate_qubit_count_during_postselection(stim.Circuit("""
        QUBIT_COORDS(0, 0) 100
        H 55 56
        M 55
        DETECTOR(0, 0, 0, 999) rec[-1]
        H 57
    """)) == 2

    assert estimate_qubit_count_during_postselection(stim.Circuit("""
        QUBIT_COORDS(0, 0) 100
        H 55 56
        M 55
        REPEAT 10 {
            H 58
        }
        DETECTOR(0, 0, 0, 999) rec[-1]
        H 57
    """)) == 3


def test_count_determined_measurements_in_circuit():
    assert count_determined_measurements_in_circuit(stim.Circuit("""
        MPP X0*X1 Y0*Y1
    """)) == 1
    assert count_determined_measurements_in_circuit(stim.Circuit("""
        MPP X0*X1 Z0*Z1 Y0*Y1
    """)) == 2
    assert count_determined_measurements_in_circuit(stim.Circuit("""
        RX 0
        MPP X0*X1 Z0*Z1 Y0*Y1
    """)) == 1
    assert count_determined_measurements_in_circuit(stim.Circuit("""
        MPP X0*X1 Z0*Z1 !Y0*Y1
    """)) == 2
    assert count_determined_measurements_in_circuit(stim.Circuit("""
        MPP X0*X1 X0 Y0*Y1
    """)) == 0
    assert count_determined_measurements_in_circuit(stim.Circuit("""
        M 0 1 2
    """)) == 3
    assert count_determined_measurements_in_circuit(stim.Circuit("""
        MX 0 1 2
        MPP X0*X1*X2
    """)) == 1

