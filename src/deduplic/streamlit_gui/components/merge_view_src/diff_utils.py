"""Diff utilities for string comparisons.

Location: src/deduplic/streamlit_gui/components/merge_view_src/diff_utils.py
"""

import difflib
import html


def render_diff_html(base_text: str, compare_text: str) -> str:
    """Genera un HTML diff destacando adiciones y eliminaciones por líneas sin tachar el texto."""
    if not base_text and not compare_text:
        return "<i style='color: #888;'>No content to compare</i>"

    base_lines = str(base_text).splitlines() if base_text else []
    compare_lines = str(compare_text).splitlines() if compare_text else []

    diff = difflib.ndiff(base_lines, compare_lines)
    diff_lines = []

    for line in diff:
        escaped_line = html.escape(line[2:])
        if line.startswith("- "):
            # ROJO SIN TACHAR (eliminaciones / texto base)
            diff_lines.append(
                f'<div style="background-color: rgba(255, 0, 0, 0.2); color: #ff6b6b; padding: 2px 4px; border-radius: 3px; margin: 1px 0; text-decoration: none !important;">- {escaped_line}</div>'
            )
        elif line.startswith("+ "):
            # VERDE (adiciones / texto a comparar)
            diff_lines.append(
                f'<div style="background-color: rgba(0, 255, 0, 0.2); color: #51cf66; padding: 2px 4px; border-radius: 3px; margin: 1px 0;">+ {escaped_line}</div>'
            )
        elif line.startswith("? "):
            continue
        else:
            diff_lines.append(f'<div style="color: #c1c2c5; padding: 2px 4px;">  {escaped_line}</div>')

    return "\n".join(diff_lines)