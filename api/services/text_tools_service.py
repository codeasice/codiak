"""
Pure business logic for text-transform tools.
No Streamlit imports — these functions can be called from FastAPI or any other context.
Extracted from the original tools/*.py render() functions.
"""

import re
import io
from typing import Optional
import pandas as pd


# ---------------------------------------------------------------------------
# HtmlToMarkdown
# ---------------------------------------------------------------------------

def html_to_markdown(html: str) -> str:
    """Convert HTML to Markdown using markdownify."""
    from markdownify import markdownify as md
    result = md(html)
    # Remove blank lines (matches original Streamlit tool behavior)
    result = "\n".join(line for line in result.splitlines() if line.strip())
    return result


# ---------------------------------------------------------------------------
# MarkdownStripper
# ---------------------------------------------------------------------------

def strip_markdown_table(text: str) -> str:
    """Strip markdown table formatting, returning cell contents as plain lines."""
    lines = text.strip().splitlines()
    output_lines = []
    for line in lines:
        if re.match(r'^\s*\|?\s*(:?-+:?\s*\|)+\s*(:?-+:?\s*)?$', line):
            continue
        if '|' in line:
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            for cell in cells:
                if cell:
                    output_lines.append(cell)
        else:
            if line.strip():
                output_lines.append(line.strip())
    return '\n'.join(output_lines)


def strip_markdown(text: str, options: dict) -> str:
    """Strip selected markdown formatting elements from text."""
    if options.get('h1'):
        text = re.sub(r'^# .+$', lambda m: m.group(0)[2:], text, flags=re.MULTILINE)
    if options.get('h2'):
        text = re.sub(r'^## .+$', lambda m: m.group(0)[3:], text, flags=re.MULTILINE)
    if options.get('h3'):
        text = re.sub(r'^### .+$', lambda m: m.group(0)[4:], text, flags=re.MULTILINE)
    if options.get('bullets'):
        text = re.sub(r'^(\s*)[-*+]\s+', r'\1', text, flags=re.MULTILINE)
    if options.get('checkboxes'):
        text = re.sub(r'^(\s*)[-*+] \[.\] ', r'\1', text, flags=re.MULTILINE)
    if options.get('bold'):
        text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)
    if options.get('italic'):
        text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)
    if options.get('inline_code'):
        text = re.sub(r'`([^`]*)`', r'\1', text)
    if options.get('code_block'):
        text = re.sub(r'```[\s\S]*?```', '', text)
    if options.get('blockquote'):
        text = re.sub(r'^>\s?', '', text, flags=re.MULTILINE)
    if options.get('hr'):
        text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)
    if options.get('table'):
        text = strip_markdown_table(text)
    return text


# ---------------------------------------------------------------------------
# ColorSwatchInjector
# ---------------------------------------------------------------------------

COLOR_SQUARE_TEMPLATE = '<span style="display:inline-block;width:1em;height:1em;background:{color};border:1px solid #888;margin-right:0.5em;vertical-align:middle;"></span>'

EXTENDED_COLORS = {
    'charcoal': '#36454F', 'brick': '#B22222', 'rust': '#B7410E',
    'terracotta': '#E2725B', 'olive': '#808000', 'moss': '#8A9A5B',
    'avocado': '#568203', 'forest': '#228B22', 'teal': '#008080',
    'turquoise': '#40E0D0', 'mustard': '#FFDB58', 'goldenrod': '#DAA520',
    'oranges': '#FFA500', 'pumpkin': '#FF7518', 'burnt': '#8A3324',
    'copper': '#B87333', 'purples': '#800080', 'eggplant': '#614051',
    'aubergine': '#472C4C', 'plum': '#8E4585', 'cinnamon': '#D2691E',
    'camel': '#C19A6B', 'espresso': '#4B3621', 'caramel': '#AF6E4D',
    'toffee': '#A47149', 'bronze': '#CD7F32', 'warm taupe': '#D2B1A3',
    'olive green': '#708238', 'espresso brown': '#4B3621', 'warm gray': '#A89F91',
    'deep brown': '#3A1F04', 'brick red': '#8B0000', 'warm burgundy': '#752E2E',
    'forest green': '#228B22', 'warm navy': '#2C3E50', 'warm gold': '#D4AF37',
    'burnt orange': '#CC5500', 'antique gold': '#C28840', 'brown-black': '#1C0D02',
    'burnt coral': '#E9897E', 'cinnamon rose': '#C16F68', 'gold': '#FFD700',
    'ivory': '#FFFFF0', 'spiced berry': '#8E3641', 'warm peach': '#FAD1AF',
    'icy blue': '#AFDBF5', 'icy silver': '#D6D9DC', 'pale pinks': '#FADADD',
    'platinum': '#E5E4E2', 'pure black': '#000000', 'silvers': '#C0C0C0',
    'stark white': '#FFFFFF', 'warm brown': '#8B5E3C',
}


def inject_color_swatches(markdown: str) -> dict:
    """
    Inject color swatch HTML into markdown color lists.
    Returns dict with 'result' (annotated markdown) and 'missing_colors' list.
    """
    header_pattern = re.compile(r'^(#+ .+)$', re.MULTILINE)
    color_line_pattern = re.compile(r'^([ \t]*[-*]?\s*)([A-Za-z][A-Za-z0-9 #,-]*)$', re.MULTILINE)
    hex_pattern = re.compile(r'^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$')

    lines = markdown.splitlines()
    output_lines = []
    in_color_section = False
    missing_colors = set()

    for line in lines:
        if header_pattern.match(line):
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
                    output_lines.append(f'{prefix}{swatch}{color}')
                elif hex_pattern.match(color.strip()):
                    swatch = COLOR_SQUARE_TEMPLATE.format(color=color.strip())
                    output_lines.append(f'{prefix}{swatch}{color}')
                else:
                    output_lines.append(line)
                    missing_colors.add(color.strip())
                continue
            if line.strip() == '' or not line.strip().startswith(('-', '*')):
                in_color_section = False
        output_lines.append(line)

    result = '\n'.join(output_lines)
    if missing_colors:
        result += '\n\n---\n**Missing color swatches for:** ' + ', '.join(sorted(missing_colors))

    return {"result": result, "missing_colors": sorted(missing_colors)}


# ---------------------------------------------------------------------------
# TableCreator
# ---------------------------------------------------------------------------

def _df_to_markdown(df: pd.DataFrame) -> str:
    return df.to_markdown(index=False)


def _parse_markdown_table(md: str) -> pd.DataFrame:
    try:
        md = md.strip()
        if md.startswith('```'):
            md = '\n'.join(l for l in md.splitlines() if not l.strip().startswith('```'))
        lines = [l for l in md.splitlines() if l.strip() and '|' in l]
        if not lines:
            return pd.DataFrame()
        if len(lines) > 1 and set(lines[1].replace('|', '').strip()) <= set('-: '):
            lines.pop(1)
        csv_lines = [','.join(c.strip() for c in l.strip('|').split('|')) for l in lines]
        return pd.read_csv(io.StringIO('\n'.join(csv_lines)))
    except Exception:
        return pd.DataFrame()


def list_to_table(input_text: str, delimiter: Optional[str] = None, force_single_column: bool = False) -> str:
    lines = [l.strip() for l in input_text.strip().splitlines() if l.strip()]
    if not lines:
        return ''
    if force_single_column:
        df = pd.DataFrame(lines, columns=["Item"])
    else:
        if delimiter is None:
            if any(',' in l for l in lines):
                delimiter = ','
            elif any('\t' in l for l in lines):
                delimiter = '\t'
        if delimiter:
            try:
                max_cols = max(len(l.split(delimiter)) for l in lines)
                padded = [delimiter.join(l.split(delimiter) + [''] * (max_cols - len(l.split(delimiter)))) for l in lines]
                df = pd.read_csv(io.StringIO('\n'.join(padded)), delimiter=delimiter)
            except Exception:
                df = pd.DataFrame(lines, columns=["Item"])
        else:
            df = pd.DataFrame(lines, columns=["Item"])
    return _df_to_markdown(df)


def join_tables(md1: str, md2: str, how: str = 'append') -> str:
    df1 = _parse_markdown_table(md1)
    df2 = _parse_markdown_table(md2)
    if df1.empty:
        return _df_to_markdown(df2)
    if df2.empty:
        return _df_to_markdown(df1)
    if how == 'append':
        df = pd.concat([df1, df2], ignore_index=True) if list(df1.columns) == list(df2.columns) \
            else pd.concat([df1, df2], ignore_index=True, sort=False)
    elif how == 'align':
        df = pd.concat([df1, df2], ignore_index=True, sort=False)
    else:
        return 'Invalid join type.'
    return _df_to_markdown(df)


# ---------------------------------------------------------------------------
# MarkdownTableConverter
# ---------------------------------------------------------------------------

def parse_markdown_table_for_converter(md: str) -> pd.DataFrame:
    try:
        md = md.strip()
        if md.startswith('```'):
            md = '\n'.join(l for l in md.splitlines() if not l.strip().startswith('```'))
        lines = [l.strip() for l in md.splitlines() if l.strip()]
        lines = [l for l in lines if not re.match(r'^\|[\s\-:]*\|[\s\-:]*\|[\s\-:]*$', l)]
        table_data = []
        for line in lines:
            if line.startswith('|') and line.endswith('|'):
                cells = [c.strip() for c in line[1:-1].split('|')]
                if not all(re.match(r'^[\s\-:]*$', c) for c in cells):
                    table_data.append(cells)
        if not table_data:
            return pd.DataFrame()
        return pd.DataFrame(table_data[1:], columns=table_data[0])
    except Exception:
        return pd.DataFrame()


def parse_excel_data(excel_text: str) -> pd.DataFrame:
    try:
        excel_text = excel_text.strip()
        if excel_text.startswith('```'):
            excel_text = '\n'.join(l for l in excel_text.splitlines() if not l.strip().startswith('```'))
        lines = [l.strip() for l in excel_text.splitlines() if l.strip()]
        if not lines:
            return pd.DataFrame()
        sep = '\t' if '\t' in lines[0] else (r'\s+' if re.search(r'\s{2,}', lines[0]) else ' ')
        table_data = []
        for line in lines:
            cells = re.split(sep, line.strip()) if sep == r'\s+' else line.split(sep)
            cells = [c.strip() for c in cells if c.strip()]
            if cells:
                table_data.append(cells)
        if not table_data:
            return pd.DataFrame()
        max_cols = max(len(r) for r in table_data)
        padded = [r + [''] * (max_cols - len(r)) for r in table_data]
        if len(padded) == 1:
            return pd.DataFrame([padded[0]], columns=[f'Column_{i+1}' for i in range(max_cols)])
        return pd.DataFrame(padded[1:], columns=padded[0])
    except Exception:
        return pd.DataFrame()


def df_to_teams_html(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    html = "<table border='1' style='border-collapse:collapse;border:1px solid #ddd;'>\n"
    html += "  <tr style='background-color:#f2f2f2;'>\n"
    for col in df.columns:
        html += f"    <th style='padding:8px;border:1px solid #ddd;text-align:left;'>{col}</th>\n"
    html += "  </tr>\n"
    for _, row in df.iterrows():
        html += "  <tr>\n"
        for val in row:
            html += f"    <td style='padding:8px;border:1px solid #ddd;'>{val}</td>\n"
        html += "  </tr>\n"
    html += "</table>"
    return html


def df_to_excel_csv(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def df_to_confluence_html(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    html = "<table class='confluenceTable'>\n  <tbody>\n    <tr>\n"
    for col in df.columns:
        html += f"      <th class='confluenceTh'>{col}</th>\n"
    html += "    </tr>\n"
    for _, row in df.iterrows():
        html += "    <tr>\n"
        for val in row:
            html += f"      <td class='confluenceTd'>{val}</td>\n"
        html += "    </tr>\n"
    html += "  </tbody>\n</table>"
    return html


def df_to_plain_text(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    col_widths = {col: max(len(str(col)), max((len(str(v)) for v in df[col]), default=0)) for col in df.columns}
    sep = "+" + "+".join("-" * (w + 2) for w in col_widths.values()) + "+"
    header = "|" + "|".join(f" {col:<{col_widths[col]}} " for col in df.columns) + "|"
    rows = ["|" + "|".join(f" {str(v):<{col_widths[col]}} " for col, v in zip(df.columns, row)) + "|"
            for _, row in df.iterrows()]
    return "\n".join([sep, header, sep] + rows + [sep])


def df_to_markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    header = "| " + " | ".join(str(c) for c in df.columns) + " |"
    separator = "| " + " | ".join("---" for _ in df.columns) + " |"
    rows = ["| " + " | ".join(str(v) for v in row) + " |" for _, row in df.iterrows()]
    return "\n".join([header, separator] + rows)


def convert_markdown_table(md: str) -> dict:
    """Convert a markdown table to all output formats."""
    df = parse_markdown_table_for_converter(md)
    if df.empty:
        return {"error": "Could not parse markdown table"}
    return {
        "teams_html": df_to_teams_html(df),
        "excel_csv": df_to_excel_csv(df),
        "confluence_html": df_to_confluence_html(df),
        "plain_text": df_to_plain_text(df),
        "row_count": len(df),
        "col_count": len(df.columns),
    }


def convert_excel_to_markdown(excel_text: str) -> dict:
    """Convert Excel/tab-separated data to a markdown table."""
    df = parse_excel_data(excel_text)
    if df.empty:
        return {"error": "Could not parse Excel data"}
    return {
        "markdown": df_to_markdown_table(df),
        "row_count": len(df),
        "col_count": len(df.columns),
    }


# ---------------------------------------------------------------------------
# ItemsToLinks
# ---------------------------------------------------------------------------

def items_to_links(input_text: str, exclude_numbers: bool = False) -> str:
    lines = input_text.strip().splitlines()
    out = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if exclude_numbers:
            s = re.sub(r'^\s*\d+[.)\-:]*\s*', '', s)
        out.append(f'[[{s}]]')
    return '\n'.join(out)


def items_to_links_bold_only(input_text: str, exclude_numbers: bool = False) -> str:
    lines = input_text.strip().splitlines()
    out = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if exclude_numbers:
            s = re.sub(r'^\s*\d+[.)\-:]*\s*', '', s)
        s = re.sub(r'\*\*(.*?)\*\*|__(.*?)__',
                   lambda m: f'[[{m.group(1) or m.group(2)}]]', s)
        out.append(s)
    return '\n'.join(out)


def links_to_items(input_text: str) -> str:
    lines = input_text.strip().splitlines()
    return '\n'.join(re.sub(r'^\[\[(.*)\]\]$', r'\1', l.strip()) for l in lines if l.strip())


# ---------------------------------------------------------------------------
# HomeAutomationCategorizer
# ---------------------------------------------------------------------------

HA_CATEGORY_MAP = {
    '.light': 'Lights',
    '.switch': 'Switches',
    '.sensor': 'Sensors',
    '.binary_sensor': 'Binary Sensors',
    '.climate': 'Climate',
    '.media_player': 'Media Players',
    '.automation': 'Automations',
    '.script': 'Scripts',
    '.scene': 'Scenes',
    '.cover': 'Covers',
    '.lock': 'Locks',
    '.alarm_control_panel': 'Alarms',
    '.camera': 'Cameras',
    '.fan': 'Fans',
    '.vacuum': 'Vacuums',
    '.input_boolean': 'Input Booleans',
    '.input_number': 'Input Numbers',
    '.input_select': 'Input Selects',
    '.input_text': 'Input Texts',
    '.input_datetime': 'Input Datetimes',
    '.group': 'Groups',
    '.person': 'Persons',
    '.zone': 'Zones',
}


def categorize_home_automation(items_text: str) -> dict:
    """
    Categorize a list of home automation items by their entity type suffix.
    Returns dict of category -> [items].
    """
    lines = [l.strip() for l in items_text.strip().splitlines() if l.strip()]
    categorized: dict[str, list[str]] = {}
    uncategorized: list[str] = []

    for item in lines:
        matched = False
        for suffix, category in HA_CATEGORY_MAP.items():
            if suffix in item.lower():
                categorized.setdefault(category, []).append(item)
                matched = True
                break
        if not matched:
            uncategorized.append(item)

    return {"categories": categorized, "uncategorized": uncategorized}
