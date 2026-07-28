import difflib

# src/streamlit_gui/utils/diff_utils.py

import difflib
import html


def render_diff_html(base_text: str, compare_text: str) -> str:
    """Genera un HTML diff destacando adiciones y eliminaciones sin tachar el texto en rojo."""
    if not base_text and not compare_text:
        return "<i style='color: #888;'>No content to compare</i>"

    # Tokenizamos/comparamos línea por línea o por palabras según tu implementación
    matcher = difflib.SequenceMatcher(None, base_text.splitlines(), compare_text.splitlines())
    
    diff_lines = []
    
    # Si la comparación es línea por línea mediante difflib.ndiff:
    diff = difflib.ndiff(base_text.splitlines(), compare_text.splitlines())
    
    for line in diff:
        escaped_line = html.escape(line[2:])
        if line.startswith("- "):
            # ROJO SIN TACHAR (background tenue o color de texto rojo destacado)
            diff_lines.append(
                f'<div style="background-color: rgba(255, 0, 0, 0.2); color: #ff6b6b; padding: 2px 4px; border-radius: 3px; margin: 1px 0; text-decoration: none !important;">- {escaped_line}</div>'
            )
        elif line.startswith("+ "):
            # VERDE (Adiciones)
            diff_lines.append(
                f'<div style="background-color: rgba(0, 255, 0, 0.2); color: #51cf66; padding: 2px 4px; border-radius: 3px; margin: 1px 0;">+ {escaped_line}</div>'
            )
        elif line.startswith("? "):
            continue
        else:
            diff_lines.append(f'<div style="color: #c1c2c5; padding: 2px 4px;">  {escaped_line}</div>')

    return "\n".join(diff_lines)