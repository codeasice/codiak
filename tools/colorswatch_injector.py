"""
ColorSwatchInjector: Augments markdown color lists with color swatches.
"""
import streamlit as st
import re
import tempfile
import os

COLOR_SQUARE_TEMPLATE = '<span style="display:inline-block;width:1em;height:1em;background:{color};border:1px solid #888;margin-right:0.5em;vertical-align:middle;"></span>'

EXTENDED_COLORS = {
    'charcoal': '#36454F',
    'brick': '#B22222',
    'rust': '#B7410E',
    'terracotta': '#E2725B',
    'olive': '#808000',
    'moss': '#8A9A5B',
    'avocado': '#568203',
    'forest': '#228B22',
    'teal': '#008080',
    'turquoise': '#40E0D0',
    'mustard': '#FFDB58',
    'goldenrod': '#DAA520',
    'oranges': '#FFA500',
    'pumpkin': '#FF7518',
    'burnt': '#8A3324',
    'copper': '#B87333',
    'purples': '#800080',
    'eggplant': '#614051',
    'aubergine': '#472C4C',
    'plum': '#8E4585',
    'cinnamon': '#D2691E',
    'camel': '#C19A6B',
    'espresso': '#4B3621',
    'caramel': '#AF6E4D',
    'toffee': '#A47149',
    'bronze': '#CD7F32',
    'warm taupe': '#D2B1A3',        # Pantone Warm Taupe 16-1318 TPX
    'olive green': '#708238',      # A classic deep olive tone
    'espresso brown': '#4B3621',   # Rich, dark brown with a coffee undertone
    'warm gray': '#A89F91',        # Warm gray with beige undertones
    'deep brown': '#3A1F04',         # Very dark, rich brown
    'brick red': '#8B0000',          # Dark red with brown undertones
    'warm burgundy': '#752E2E',      # Burgundy with added warmth (more red/orange)
    'forest green': '#228B22',       # Deep, saturated natural green
    'warm navy': '#2C3E50',          # Navy with subtle warmth (slightly muted blue)
    'warm gold': '#D4AF37',          # Lush, warm gold tone
    'burnt orange': '#CC5500',       # Strong reddish-orange, earthy and bold
    'antique gold': '#C28840',      # Muted, aged golden tone
    'brown-black': '#1C0D02',       # Nearly black with brown undertones
    'burnt coral': '#E9897E',       # Muted red-orange coral with a toasted feel
    'cinnamon rose': '#C16F68',     # Rosy reddish brown, rich and warm
    'gold': '#FFD700',              # Classic bright gold
    'ivory': '#FFFFF0',             # Off-white with yellow/beige tone
    'spiced berry': '#8E3641',      # Deep red with warm, spiced tone
    'warm peach': '#FAD1AF',        # Soft, creamy peach with a warm glow
    'icy blue': '#AFDBF5',          # Light, cool-toned blue with a frosty feel
    'icy silver': '#D6D9DC',        # Very light gray with a cold, metallic edge
    'pale pinks': '#FADADD',        # Soft blush tone (interpreted as a single color)
    'platinum': '#E5E4E2',          # Very light metallic gray
    'pure black': '#000000',        # Absolute black
    'silvers': '#C0C0C0',           # Neutral silver tone
    'stark white': '#FFFFFF',       # True white with no warmth
    'warm brown': '#8B5E3C',        # Brown with strong orange/red undertones
}


def inject_color_swatches(markdown):
    # Pattern: header (## or #) followed by a list of color names (one per line, optionally with - or *)
    header_pattern = re.compile(r'^(#+ .+)$', re.MULTILINE)
    color_line_pattern = re.compile(r'^([ \t]*[-*]?\s*)([A-Za-z][A-Za-z0-9 #,-]*)$', re.MULTILINE)

    lines = markdown.splitlines()
    output_lines = []
    in_color_section = False
    missing_colors = set()
    hex_pattern = re.compile(r'^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$')

    for i, line in enumerate(lines):
        header_match = header_pattern.match(line)
        if header_match:
            in_color_section = True
            output_lines.append(line)
            continue
        if in_color_section:
            color_match = color_line_pattern.match(line)
            if color_match:
                prefix, color = color_match.groups()
                color_key = color.strip().lower()
                color_value = EXTENDED_COLORS.get(color_key)
                if color_value:
                    swatch = COLOR_SQUARE_TEMPLATE.format(color=color_value)
                    new_line = f'{prefix}{swatch}{color}'
                    output_lines.append(new_line)
                elif hex_pattern.match(color.strip()):
                    swatch = COLOR_SQUARE_TEMPLATE.format(color=color.strip())
                    new_line = f'{prefix}{swatch}{color}'
                    output_lines.append(new_line)
                else:
                    # Missing color: show no swatch, add to missing list
                    output_lines.append(line)
                    missing_colors.add(color.strip())
                continue
            # End color section if line is empty or not a color
            if line.strip() == '' or not line.strip().startswith(('-', '*')):
                in_color_section = False
        output_lines.append(line)
    # Add summary of missing colors if any
    if missing_colors:
        output_lines.append('\n---')
        output_lines.append('**Missing color swatches for:** ' + ', '.join(sorted(missing_colors)))
    return '\n'.join(output_lines)


def render():
    st.write("Paste your markdown with color lists below. Each color name will be augmented with a colored square.")
    st.info("Headers (e.g. ## Colors) followed by lists of color names (one per line, optionally with - or *) will be processed. Supports common color names and hex codes.")

    input_text = st.text_area(
        "Markdown Input:",
        value="## My Colors\n- red\n- green\n- blue\n- #ffcc00\n- #333\n",
        height=200,
        key="colorswatch_input",
    )
    process_btn = st.button("Inject Color Swatches", key="colorswatch_btn")
    output = ""
    if process_btn:
        output = inject_color_swatches(input_text)
    st.markdown(
        "**Output (with color swatches):**",
        unsafe_allow_html=True
    )
    st.text_area(
        "Output Markdown:",
        value=output or "",
        height=200,
        key="colorswatch_output",
    )
    if output:
        st.markdown(output, unsafe_allow_html=True)
        # PDF generation section
        st.divider()
        st.subheader("Export")
        if st.button("Download PDF", key="download_pdf_btn"):
            try:
                import pdfkit
                # Convert markdown output to HTML for PDF rendering
                html_body = output.replace('\n', '<br>')
                html_content = f"<html><body>{html_body}</body></html>"
                pdf_bytes = pdfkit.from_string(html_content, False)
                st.download_button(
                    label="Download PDF File",
                    data=pdf_bytes,
                    file_name="color_swatch_output.pdf",
                    mime="application/pdf"
                )
            except ImportError:
                st.error("pdfkit is not installed. Please install it with 'pip install pdfkit' and ensure wkhtmltopdf is available.")
            except Exception as e:
                st.error(f"PDF generation failed: {e}")