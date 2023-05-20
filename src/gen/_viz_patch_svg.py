import math
from typing import Iterable, List, Union, Literal, TYPE_CHECKING

from gen._patch import Patch

if TYPE_CHECKING:
    import gen


def patch_svg_viewer(
        patches: Iterable[Patch],
        *,
        canvas_height: int = 500,
        show_order: Union[bool, Literal['undirected', '3couplerspecial']] = True,
        opacity: float = 1,
        show_measure_qubits: bool = True,
        show_data_qubits: bool = False,
        available_qubits: Iterable[complex] = (),
        extra_used_coords: Iterable[complex] = ()) -> str:
    """Returns a picture of the stabilizers measured by various plan.
    """
    available_qubits = frozenset(available_qubits)
    extra_used_coords = frozenset(extra_used_coords)
    patches = tuple(patches)
    boxes = [plan.bounding_box(available_qubits | extra_used_coords) for plan in patches]
    box_width = max(((b - a).real for a, b in boxes), default=0)
    box_height = max(((b - a).imag for a, b in boxes), default=0)
    pad = max(box_width, box_height) * 0.1 + 1
    box_width += pad
    box_height += pad
    height = max(1, box_height)
    width = max(1, box_width * len(patches))
    scale_factor = canvas_height / max(height, 1)
    canvas_width = int(math.ceil(canvas_height * (width / height)))

    def transform_pt(plan_i2: int, pt2: complex) -> complex:
        min_ri = boxes[plan_i2][0]
        pt2 -= min_ri
        pt2 += box_width * plan_i2
        pt2 += pad * (0.5 + 0.5j)
        pt2 *= scale_factor
        return pt2

    def transform_dif(dif: complex) -> complex:
        return dif * scale_factor

    def pt(plan_i2: int, q2: complex) -> str:
        return f"{transform_pt(plan_i2, q2).real},{transform_pt(plan_i2, q2).imag}"

    def dt(q2: complex) -> str:
        return f"{transform_dif(q2).real},{transform_dif(q2).imag}"

    lines = [
        f"""<svg viewBox="0 0 {canvas_width} {canvas_height}" xmlns="http://www.w3.org/2000/svg">"""]

    # Draw each plan element as a polygon.
    clip_path_id = 0
    BASE_COLORS = {"X": '#FF8080', "Z": '#8080FF', "Y": '#80FF80', None: "gray"}

    lines.append(f'<rect fill="{BASE_COLORS["X"]}" x="1" y="1" width="20" height="20" />')
    lines.append(
        '<text'
        ' x="11"'
        ' y="11"'
        ' fill="white"'
        ' font-size="20"'
        ' text-anchor="middle"'
        ' alignment-baseline="central"'
        '>X</text>'
    )

    lines.append(
        f'<rect fill="{BASE_COLORS["Z"]}" x="1" y="21" width="20" height="20" />'
    )
    lines.append(
        '<text'
        ' x="11"'
        ' y="31"'
        ' fill="white"'
        ' font-size="20"'
        ' text-anchor="middle"'
        ' alignment-baseline="central"'
        '>Z</text>'
    )

    layer_1q2 = []
    layer_1q = []
    fill_layer2q = []
    stroke_layer2q = []
    fill_layer_mq = []
    stroke_layer_mq = []
    def data_span(tile: 'gen.Tile') -> float:
        min_r = min(q.real for q in tile.data_set)
        min_i = min(q.imag for q in tile.data_set)
        max_r = max(q.real for q in tile.data_set)
        max_i = max(q.imag for q in tile.data_set)
        return max_r - min_r + max_i - min_i

    for plan_i, plan in enumerate(patches):
        sorted_tiles = sorted(plan.tiles, key=data_span, reverse=True)
        for tile in sorted_tiles:
            c = tile.measurement_qubit
            if True or any(abs(q - c) < 1e-4 for q in tile.data_set):
                c = sum(tile.data_set) / len(tile.data_set)
            dq = sorted(
                tile.data_set,
                key=lambda p2: math.atan2(p2.imag - c.imag, p2.real - c.real),
            )
            if not dq:
                continue
            common_basis = tile.basis
            fill_color = BASE_COLORS[common_basis]

            if len(dq) == 1:
                p = transform_pt(plan_i, dq[0])
                layer_1q.append(f'<circle '
                                f'cx="{p.real}" '
                                f'cy="{p.imag}" '
                                f'r="{transform_dif(0.2).real}" '
                                f'fill="{BASE_COLORS[tile.bases[0]]}" '
                                f'stroke="yellow" />')
                path_cmd_start = None
            elif len(dq) == 2:
                a, b = dq
                da = a - c
                db = b - c
                dab = math.atan2(da.imag, da.real) - math.atan2(db.imag, db.real)
                dab %= math.pi * 2
                if dab < math.pi:
                    a, b = b, a

                path_cmd_start = (f'<path '
                     f'd="M{pt(plan_i, a)} '
                     f'a1,1 '
                     f'0 0,0 '
                     f'{dt(b - a)} '
                     f'L{pt(plan_i, a)}"')

                if abs(abs(da) - abs(db)) > 1e-4 or abs(da + db) < 1e-4:
                    # Draw wedges instead of oriented semicircles when not nicely aligned.
                    dif = b - a
                    average = (a + b) * 0.5
                    perp = dif * 1j
                    if abs(perp) > 1:
                        perp /= abs(perp)
                    ac1 = average + perp * 0.2 - dif * 0.2
                    ac2 = average + perp * 0.2 + dif * 0.2
                    bc1 = average + perp * -0.2 + dif * 0.2
                    bc2 = average + perp * -0.2 - dif * 0.2

                    tac1 = transform_pt(plan_i, ac1)
                    tac2 = transform_pt(plan_i, ac2)
                    tbc1 = transform_pt(plan_i, bc1)
                    tbc2 = transform_pt(plan_i, bc2)
                    ta = transform_pt(plan_i, a)
                    tb = transform_pt(plan_i, b)
                    path_cmd_start = (f'<path '
                         f'd="M{pt(plan_i, a)} '
                         f'C {tac1.real} {tac1.imag}, '
                         f'{tac2.real} {tac2.imag}, '
                         f'{tb.real} {tb.imag} '
                         f'C {tbc1.real} {tbc1.imag}, '
                         f'{tbc2.real} {tbc2.imag}, '
                         f'{ta.real} {ta.imag} '
                         f'"')

                fill_layer2q.append(f'{path_cmd_start} '
                             f'fill="{fill_color}" '
                                    f'''stroke="{'black' if show_order != 'undirected' else 'none'}" />''')
                if show_order != 'undirected':
                    stroke_layer2q.append(f'{path_cmd_start} '
                                 f'fill="{fill_color}" '
                                 f'stroke="black" />')
            else:
                path_cmd_start = f'<path d="M{pt(plan_i, dq[-1])}'
                for q in dq:
                    path_cmd_start += ' ' + pt(plan_i, q)
                path_cmd_start += '"'
                fill_layer_mq.append(f'{path_cmd_start} fill="{fill_color}" opacity="{opacity}" stroke="none" />')
                if show_order != 'undirected':
                    stroke_layer_mq.append(f'{path_cmd_start} stroke="black" fill="none" />')

            if show_measure_qubits:
                m = tile.measurement_qubit
                if show_order == 'undirected':
                    m = m * 0.8 + c * 0.2
                p = transform_pt(plan_i, m)
                layer_1q2.append(f'<circle '
                                f'cx="{p.real}" '
                                f'cy="{p.imag}" '
                                f'r="{transform_dif(0.05).real}" '
                                f'fill="black" '
                                f'''stroke="{'black' if show_order != 'undirected' else 'none'}" />''')
            if show_data_qubits:
                for d in tile.data_set:
                    p = transform_pt(plan_i, d)
                    layer_1q2.append(f'<circle '
                                     f'cx="{p.real}" '
                                     f'cy="{p.imag}" '
                                     f'r="{transform_dif(0.1).real}" '
                                     f'fill="black" '
                                     f'''stroke="{'black' if show_order != 'undirected' else 'none'}" />''')

            if common_basis is None and path_cmd_start is not None:
                clip_path_id += 1
                fill_layer_mq.append(f'<clipPath id="clipPath{clip_path_id}">')
                fill_layer_mq.append(f'    {path_cmd_start} />')
                fill_layer_mq.append(f'</clipPath>')
                for k, q in enumerate(tile.ordered_data_qubits):
                    if q is None:
                        continue
                    v = transform_pt(plan_i, q)
                    fill_layer_mq.append(f'<circle '
                                 f'clip-path="url(#clipPath{clip_path_id})" '
                                 f'cx="{v.real}" '
                                 f'cy="{v.imag}" '
                                 f'r="{transform_dif(0.45).real}" '
                                 f'fill="{BASE_COLORS[tile.bases[k]]}" '
                                 f'stroke="none" />')
    lines += fill_layer_mq + stroke_layer_mq + fill_layer2q + stroke_layer2q + layer_1q + layer_1q2

    # Draw each element's measurement order as a zig zag arrow.
    assert show_order in [False, True, '3couplerspecial', 'undirected']
    if show_order:
        for plan_i, plan in enumerate(patches):
            for tile in plan.tiles:
                c = tile.measurement_qubit
                if len(tile.data_set) == 3 or c in tile.data_set:
                    c = 0
                    for q in tile.data_set:
                        c += q
                    c /= len(tile.data_set)
                pts: List[complex] = []

                path_cmd_start = f'<path d="M'
                arrow_color = "black"
                delay = 0
                prev = None
                for q in tile.ordered_data_qubits:
                    if q is not None:
                        f = 0.6 if show_order != 'undirected' else 0.8
                        v = q * f + c * (1 - f)
                        path_cmd_start += pt(plan_i, v) + ' '
                        v = transform_pt(plan_i, v)
                        pts.append(v)
                        for d in range(delay):
                            if prev is None:
                                prev = v
                            v2 = (prev + v) / 2
                            lines.append(
                                f'<circle cx="{v2.real}" cy="{v2.imag}" r="{transform_dif(d * 0.06 + 0.04).real}" stroke="yellow" fill="none" />')
                        delay = 0
                        prev = v
                    else:
                        delay += 1
                path_cmd_start = path_cmd_start.strip()
                path_cmd_start += f'" fill="none" stroke="{arrow_color}" />'
                lines.append(path_cmd_start)

                # Draw arrow at end of arrow.
                if show_order is True and len(pts) > 1:
                    p = pts[-1]
                    d2 = p - pts[-2]
                    if d2:
                        d2 /= abs(d2)
                        d2 *= 4
                    a = p + d2
                    b = p + d2 * 1j
                    c = p + d2 * -1j
                    lines.append(
                        f'<path'
                        f' d="M{a.real},{a.imag} {b.real},{b.imag} {c.real},{c.imag} {a.real},{a.imag}"'
                        f' stroke="none"'
                        f' fill="{arrow_color}" />'
                    )
                if show_order == '3couplerspecial' and len(pts) > 2:
                    # Show location of measurement qubit.
                    p = transform_pt(plan_i, tile.ordered_data_qubits[-2] * 0.6 + c * 0.4)
                    lines.append(f'<circle '
                                 f'cx="{p.real}" '
                                 f'cy="{p.imag}" '
                                 f'r="{transform_dif(0.02).real}" '
                                 f'fill="black" '
                                 f'stroke="black" />')

    if available_qubits | extra_used_coords:
        for plan_i, plan in enumerate(patches):
            for q in available_qubits | (plan.used_set | extra_used_coords):
                fill_color = 'black' if q in available_qubits else 'orange'
                if not show_measure_qubits and not q in available_qubits and q in plan.measure_set:
                    continue
                q2 = transform_pt(plan_i, q)
                lines.append(
                    f'<circle'
                    f' cx="{q2.real}"'
                    f' cy="{q2.imag}"'
                    f' fill="{fill_color}"'
                    f' stroke="white"'
                    f' r="{transform_dif(0.2).real}"'
                    f'/>'
                )
    lines.append("</svg>")
    return "\n".join(lines)
