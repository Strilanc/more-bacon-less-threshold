import math
from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from gen._surface_code import BoundaryList


def boundary_list_svg_viewer(
        values: Iterable['BoundaryList'],
        *,
        canvas_height: int = 500) -> str:
    """Returns a picture of the stabilizers measured by various plan.
    """
    boundary_lists = tuple(values)
    points = [p for bl in boundary_lists for curve in bl.curves for p in curve.points]
    min_r = min([p.real for p in points], default=0)
    min_i = min([p.imag for p in points], default=0)
    max_r = max([p.real for p in points], default=0)
    max_i = max([p.imag for p in points], default=0)
    box_width = max_r - min_r
    box_height = max_i - min_i
    pad = max(box_width, box_height) * 0.1 + 1
    box_width += pad
    box_height += pad
    height = max(1, box_height)
    width = max(1, box_width * len(boundary_lists))
    scale_factor = canvas_height / max(height, 1)
    canvas_width = int(math.ceil(canvas_height * (width / height)))
    stroke_width = scale_factor / 25

    def transform_pt(plan_i2: int, pt2: complex) -> complex:
        pt2 += box_width * plan_i2
        pt2 += pad * (0.5 + 0.5j)
        pt2 *= scale_factor
        return pt2

    lines = [
        f"""<svg viewBox="0 0 {canvas_width} {canvas_height}" xmlns="http://www.w3.org/2000/svg">"""]

    BASE_COLORS = {"X": '#FF0000', "Z": '#0000FF', "Y": '#00FF00', None: "gray"}

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
        f'<rect fill="{BASE_COLORS["Y"]}" x="1" y="21" width="20" height="20" />'
    )
    lines.append(
        '<text'
        ' x="11"'
        ' y="31"'
        ' fill="white"'
        ' font-size="20"'
        ' text-anchor="middle"'
        ' alignment-baseline="central"'
        '>Y</text>'
    )

    lines.append(
        f'<rect fill="{BASE_COLORS["Z"]}" x="1" y="41" width="20" height="20" />'
    )
    lines.append(
        '<text'
        ' x="11"'
        ' y="51"'
        ' fill="white"'
        ' font-size="20"'
        ' text-anchor="middle"'
        ' alignment-baseline="central"'
        '>Z</text>'
    )

    # Draw interior.
    for bl_i, bl in enumerate(boundary_lists):
        pieces = []
        for curve in bl.curves:
            pieces.append('M')
            for k in range(len(curve)):
                a = transform_pt(bl_i, curve.points[k])
                pieces.append(f'{a.real},{a.imag}')
        pieces.append('Z')
        path = ' '.join(pieces)
        lines.append(f'<path d="{path}" fill="#ddd" stroke="none"/>')

    # Trace boundaries.
    for bl_i, bl in enumerate(boundary_lists):
        for curve in bl.curves:
            for k in range(len(curve)):
                a = transform_pt(bl_i, curve.points[k - 1])
                b = transform_pt(bl_i, curve.points[k])
                stroke_color = BASE_COLORS[curve.bases[k]]
                lines.append(f'<line '
                             f'x1="{a.real}" '
                             f'y1="{a.imag}" '
                             f'x2="{b.real}" '
                             f'y2="{b.imag}" '
                             f'stroke-width="{stroke_width * 8}" '
                             f'stroke="{stroke_color}" />')

    # Trace control points.
    for bl_i, bl in enumerate(boundary_lists):
        for curve in bl.curves:
            for k in range(len(curve)):
                a = transform_pt(bl_i, curve.points[k])
                lines.append(f'<circle '
                             f'cx="{a.real}" '
                             f'cy="{a.imag}" '
                             f'r="{stroke_width * 5}" '
                             f'stroke-width="{stroke_width}" '
                             f'fill="black" '
                             f'stroke="black" />')

    # for bl_i, v in enumerate(values):
    #     if not isinstance(v, SkeletonWithMerges):
    #         continue
    #     for a, b in v.merges:
    #         a = transform_pt(bl_i, v.skeleton.centers[a])
    #         b = transform_pt(bl_i, v.skeleton.centers[b])
    #         stroke_color = 'black'
    #         lines.append(f'<line '
    #                      f'x1="{a.real}" '
    #                      f'y1="{a.imag}" '
    #                      f'x2="{b.real}" '
    #                      f'y2="{b.imag}" '
    #                      f'stroke-width="{stroke_width * 16}" '
    #                      f'stroke="{stroke_color}" />')

    lines.append("</svg>")
    return "\n".join(lines)
