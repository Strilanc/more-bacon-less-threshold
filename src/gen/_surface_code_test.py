from gen._boundary_list import Order_Z, Order_ᴎ, checkerboard_basis
from gen._builder import Builder
from gen._surface_code import Curve, BoundaryList, layer_transition, surface_code_patch


def test_surface_code_patch():
    patch = surface_code_patch(
        width=5,
        height=5,
        top_basis='Z',
        bot_basis='Z',
        left_basis='X',
        right_basis='X',
        rel_order_func=lambda _: Order_Z,
    )
    assert len(patch.data_set) == 25
    assert len(patch.tiles) == 24


def test_layer_transition_notched_shift():
    c0 = Curve()
    c0.line_to('Z', 6 + 0j)
    c0.line_to('X', 6 + 6j)
    c0.line_to('Z', 0 + 6j)
    c0.line_to('X', 0 + 0j)
    p0 = BoundaryList([c0]).to_plan(rel_order_func=lambda m: Order_Z if checkerboard_basis(m) == 'Z' else Order_ᴎ)
    p2 = BoundaryList([c0.offset_by(2)]).to_plan(rel_order_func=lambda m: Order_Z if checkerboard_basis(m) == 'Z' else Order_ᴎ)
    p3 = BoundaryList([c0.offset_by(3)]).to_plan(rel_order_func=lambda m: Order_Z if checkerboard_basis(m) == 'Z' else Order_ᴎ)

    builder = Builder.for_qubits(p0.used_set | p3.used_set | {-1})

    builder.measure_pauli_product(zs=[q for q in p0.data_set if q.real == 4] + [-1], key="H_INIT")
    builder.obs_include(["H_INIT"], obs_index=2)
    builder.tick()
    builder.measure_pauli_product(xs=[q for q in p0.data_set if q.imag == 0] + [-1], key="V_INIT")
    builder.obs_include(["V_INIT"], obs_index=5)
    builder.tick()

    p0.measure(style='mpp', builder=builder, save_layer=4)

    builder.tick()
    layer_transition(
        builder=builder,
        past_patch=p0,
        future_patch=p2,
        kept_data_qubits=p0.data_set & p2.data_set & p3.data_set,
        style='mpp',
        past_compare_layer=4,
        past_save_layer=5,
        future_save_layer=6,
        past_layer_lost_data_obs_qubit_sets={
            2: {q for q in p0.data_set | p3.data_set if q.real == 4},
            5: {q for q in p0.data_set | p3.data_set if q.imag == 0},
        },
        future_layer_gain_data_reset_basis='X',
        past_layer_lost_data_measure_basis='X',
    )

    builder.measure_pauli_product(zs=[q for q in p2.data_set if q.real == 4] + [-1], key="H_OUT")
    builder.obs_include(["H_OUT"], obs_index=2)
    builder.tick()
    builder.measure_pauli_product(xs=[q for q in p2.data_set if q.imag == 0] + [-1], key="V_OUT")
    builder.obs_include(["V_OUT"], obs_index=5)
    builder.tick()

    # Verify that all detectors and observables are deterministic.
    builder.circuit.detector_error_model(decompose_errors=True)


def test_layer_transition_shrink():
    c_shrunk = Curve()
    c_shrunk.line_to('X', 3 + 0j)
    c_shrunk.line_to('Z', 3 + 6j)
    c_shrunk.line_to('X', 0 + 6j)
    c_shrunk.line_to('Z', 0 + 0j)

    c_full = Curve()
    c_full.line_to('X', 6 + 0j)
    c_full.line_to('Z', 6 + 6j)
    c_full.line_to('X', 0 + 6j)
    c_full.line_to('Z', 0 + 0j)

    p_shrunk = BoundaryList([c_shrunk]).to_plan(rel_order_func=lambda m: Order_Z if checkerboard_basis(m) == 'Z' else Order_ᴎ)
    p_full = BoundaryList([c_full]).to_plan(rel_order_func=lambda m: Order_Z if checkerboard_basis(m) == 'Z' else Order_ᴎ)

    builder = Builder.for_qubits(p_full.used_set | {-1})

    builder.measure_pauli_product(xs=[q for q in p_full.data_set if q.real == 0] + [-1], key="H_INIT")
    builder.obs_include(["H_INIT"], obs_index=2)
    builder.tick()
    builder.measure_pauli_product(zs=[q for q in p_full.data_set if q.imag == 0] + [-1], key="V_INIT")
    builder.obs_include(["V_INIT"], obs_index=5)
    builder.tick()

    p_full.measure(style='mpp', builder=builder, save_layer=4)

    builder.tick()
    layer_transition(
        builder=builder,
        past_patch=p_full,
        future_patch=p_shrunk,
        kept_data_qubits=p_shrunk.data_set,
        style='mpp',
        past_compare_layer=4,
        past_save_layer=5,
        future_save_layer=6,
        past_layer_lost_data_obs_qubit_sets={
            2: {q for q in p_full.data_set if q.real == 0},
            5: {q for q in p_full.data_set if q.imag == 0},
        },
        past_layer_lost_data_measure_basis='Z',
        future_layer_gain_data_reset_basis='Z',
    )

    builder.measure_pauli_product(xs=[q for q in p_shrunk.data_set if q.real == 0] + [-1], key="H_OUT")
    builder.obs_include(["H_OUT"], obs_index=2)
    builder.tick()
    builder.measure_pauli_product(zs=[q for q in p_shrunk.data_set if q.imag == 0] + [-1], key="V_OUT")
    builder.obs_include(["V_OUT"], obs_index=5)
    builder.tick()

    # Verify that all detectors and observables are deterministic.
    builder.circuit.detector_error_model(decompose_errors=True)


def test_layer_transition_full_notch():
    c = Curve()
    c.line_to('X', 3 + 0j)
    c.line_to('Z', 3 + 3j)
    c.line_to('X', 0 + 3j)
    c.line_to('Z', 0 + 0j)

    p = BoundaryList([c]).to_plan(rel_order_func=lambda m: Order_Z if checkerboard_basis(m) == 'Z' else Order_ᴎ)
    builder = Builder.for_qubits(p.used_set)
    p.measure(style='mpp', builder=builder, save_layer=4)
    builder.tick()
    layer_transition(
        builder=builder,
        past_patch=p,
        future_patch=p,
        kept_data_qubits=set(),
        style='mpp',
        past_compare_layer=4,
        past_save_layer=5,
        future_save_layer=6,
        past_layer_lost_data_obs_qubit_sets={},
        past_layer_lost_data_measure_basis='Z',
        future_layer_gain_data_reset_basis='Z',
    )

    # Verify that all detectors and observables are deterministic.
    builder.circuit.detector_error_model(decompose_errors=True)
    assert builder.circuit.num_detectors == 7 * 3 + 8


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


def test_distance_2():
    curve = Curve(points=[1, (1 + 1j), 1j, 0], bases='ZXZX')
    plan = BoundaryList([curve]).to_plan(rel_order_func=lambda _: Order_Z)
    assert len(plan.tiles) == 3