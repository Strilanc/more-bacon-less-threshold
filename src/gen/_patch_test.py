import stim

from gen._builder import Builder
from gen._patch import Patch
from gen._tile import Tile


def test_just_do_cz_measurements():
    builder = Builder.for_qubits([0, 1, 2])
    builder.circuit.clear()
    Patch([
        Tile(
            bases='Z',
            measurement_qubit=0,
            ordered_data_qubits=(1,),
        ),
    ]).measure(
        data_resets={1: 'Y'},
        data_measures={},
        builder=builder,
        save_layer=0,
    )
    assert builder.circuit == stim.Circuit("""
        R 0 1
        TICK
        C_ZYX 1
        H 0
        TICK
        CZ 0 1
        TICK
        H 0
        TICK
        M 0
    """)

    builder.circuit.clear()
    Patch([
        Tile(
            bases='X',
            measurement_qubit=0,
            ordered_data_qubits=(1,),
        ),
    ]).measure(
        data_resets={1: 'Y'},
        data_measures={},
        builder=builder,
        save_layer=1,
    )
    assert builder.circuit == stim.Circuit("""
        R 0 1
        TICK
        H 0
        H_XY 1
        TICK
        CZ 0 1
        TICK
        H 0 1
        TICK
        M 0
    """)

    builder.circuit.clear()
    Patch([
        Tile(
            bases='X',
            measurement_qubit=0,
            ordered_data_qubits=(1, 2),
        )
    ]).measure(
        data_resets={1: 'Y', 2: 'Y'},
        data_measures={},
        builder=builder,
        save_layer=2,
    )
    assert builder.circuit == stim.Circuit("""
        R 0 1 2
        TICK
        H 0
        H_XY 1 2
        TICK
        CZ 0 1
        TICK
        CZ 0 2
        TICK
        H 0 1 2
        TICK
        M 0
    """)


def test_do_cz_measurements():
    plan = Patch([
        Tile(
            bases='X',
            measurement_qubit=0,
            ordered_data_qubits=(-1 - 1j, +1 - 1j, None, +1 + 1j),
        ),
        Tile(
            bases='Z',
            measurement_qubit=2,
            ordered_data_qubits=tuple(2 + d for d in [-1 - 1j, -1 + 1j, +1 - 1j, +1 + 1j]),
        ),
    ])
    builder = Builder.for_qubits(plan.used_set)
    builder.circuit.clear()
    plan.detect(
        data_resets={q: 'Y' for q in plan.data_set},
        skipped_comparisons={0},
        comparison_overrides={2: []},
        data_measures={},
        builder=builder,
        tracker_layer=0,
    )
    assert builder.circuit == stim.Circuit("""
        R 0 1 2 3 4 5 6
        TICK
        C_ZYX 2
        H 1 4
        H_XY 0
        TICK
        CZ 0 1 2 4
        TICK
        C_ZYX 3 5
        H 2
        TICK
        CZ 1 2 3 4
        TICK
        CZ 4 5
        TICK
        C_ZYX 6
        H 3
        TICK
        CZ 1 3 4 6
        TICK
        H 0 1 2 3 4
        TICK
        M 1 4
        DETECTOR(2, 0, 0) rec[-1]
        SHIFT_COORDS(0, 0, 1)
    """)
