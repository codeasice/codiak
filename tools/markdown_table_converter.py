#!/usr/bin/env python3
"""
Markdown Table Converter Tool

Converts markdown tables to formats compatible with:
- Microsoft Teams (HTML table)
- Excel (CSV format)
- Confluence (HTML table)

Also converts Excel-like data to markdown format.
"""

import streamlit as st
import pandas as pd
import io
import re

def parse_markdown_table(md: str) -> pd.DataFrame:
    """
    Parses a markdown table string into a pandas DataFrame.
    """
    try:
        # Remove code block markers if present
        md = md.strip()
        if md.startswith('```'):
            md = '\n'.join(line for line in md.splitlines() if not line.strip().startswith('```'))

        # Split into lines and filter out empty lines
        lines = [line.strip() for line in md.splitlines() if line.strip()]
        if not lines:
            return pd.DataFrame()

        # Remove separator line (e.g. |---|---|)
        lines = [line for line in lines if not re.match(r'^\|[\s\-:]*\|[\s\-:]*\|[\s\-:]*$', line)]

        # Parse table rows
        table_data = []
        for line in lines:
            if line.startswith('|') and line.endswith('|'):
                # Remove leading/trailing pipes and split
                cells = [cell.strip() for cell in line[1:-1].split('|')]
                # Skip separator lines (lines that are mostly dashes)
                if not all(re.match(r'^[\s\-:]*$', cell) for cell in cells):
                    table_data.append(cells)

        if not table_data:
            return pd.DataFrame()

        # Create DataFrame
        df = pd.DataFrame(table_data[1:], columns=table_data[0])
        return df

    except Exception as e:
        st.error(f"Error parsing markdown table: {e}")
        return pd.DataFrame()

def parse_excel_data(excel_text: str) -> pd.DataFrame:
    """
    Parses Excel-like data (tab-separated or space-separated) into a pandas DataFrame.
    """
    try:
        # Remove code block markers if present
        excel_text = excel_text.strip()
        if excel_text.startswith('```'):
            excel_text = '\n'.join(line for line in excel_text.splitlines() if not line.strip().startswith('```'))

        # Split into lines and filter out empty lines
        lines = [line.strip() for line in excel_text.splitlines() if line.strip()]
        if not lines:
            return pd.DataFrame()

        # Try to detect the separator
        # First, try tab separation (most common Excel paste format)
        if '\t' in lines[0]:
            separator = '\t'
        else:
            # Try to detect space separation by looking for multiple spaces
            if re.search(r'\s{2,}', lines[0]):
                separator = r'\s+'
            else:
                separator = ' '

        # Parse table rows
        table_data = []
        for line in lines:
            if separator == r'\s+':
                # Handle multiple spaces
                cells = re.split(separator, line.strip())
            else:
                # Handle tab or single space
                cells = line.split(separator)

            # Clean up cells and filter out empty ones
            cells = [cell.strip() for cell in cells if cell.strip()]
            if cells:  # Only add non-empty rows
                table_data.append(cells)

        if not table_data:
            return pd.DataFrame()

        # Find the maximum number of columns
        max_cols = max(len(row) for row in table_data)

        # Pad rows with fewer columns
        padded_data = []
        for row in table_data:
            padded_row = row + [''] * (max_cols - len(row))
            padded_data.append(padded_row)

        # Create DataFrame
        if len(padded_data) == 1:
            # Single row, create DataFrame with generic column names
            df = pd.DataFrame([padded_data[0]], columns=[f'Column_{i+1}' for i in range(max_cols)])
        else:
            # Multiple rows, use first row as headers
            df = pd.DataFrame(padded_data[1:], columns=padded_data[0])

        return df

    except Exception as e:
        st.error(f"Error parsing Excel data: {e}")
        return pd.DataFrame()

def to_teams_html(df: pd.DataFrame) -> str:
    """
    Converts DataFrame to HTML table format suitable for Teams.
    """
    if df.empty:
        return ""

    html = "<table border='1' style='border-collapse: collapse; border: 1px solid #ddd;'>\n"

    # Header row
    html += "  <tr style='background-color: #f2f2f2;'>\n"
    for col in df.columns:
        html += f"    <th style='padding: 8px; border: 1px solid #ddd; text-align: left;'>{col}</th>\n"
    html += "  </tr>\n"

    # Data rows
    for _, row in df.iterrows():
        html += "  <tr>\n"
        for value in row:
            html += f"    <td style='padding: 8px; border: 1px solid #ddd;'>{value}</td>\n"
        html += "  </tr>\n"

    html += "</table>"
    return html

def to_excel_csv(df: pd.DataFrame) -> str:
    """
    Converts DataFrame to CSV format suitable for Excel.
    """
    if df.empty:
        return ""

    # Convert to CSV string
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue()

def to_confluence_html(df: pd.DataFrame) -> str:
    """
    Converts DataFrame to HTML table format suitable for Confluence.
    """
    if df.empty:
        return ""

    html = "<table class='confluenceTable'>\n"

    # Header row
    html += "  <tbody>\n    <tr>\n"
    for col in df.columns:
        html += f"      <th class='confluenceTh'>{col}</th>\n"
    html += "    </tr>\n"

    # Data rows
    for _, row in df.iterrows():
        html += "    <tr>\n"
        for value in row:
            html += f"      <td class='confluenceTd'>{value}</td>\n"
        html += "    </tr>\n"

    html += "  </tbody>\n</table>"
    return html

def to_plain_text(df: pd.DataFrame) -> str:
    """
    Converts DataFrame to plain text format with simple formatting.
    """
    if df.empty:
        return ""

    # Get column widths
    col_widths = {}
    for col in df.columns:
        max_width = len(str(col))
        for value in df[col]:
            max_width = max(max_width, len(str(value)))
        col_widths[col] = max_width

    # Build table
    lines = []

    # Header separator
    separator = "+" + "+".join("-" * (width + 2) for width in col_widths.values()) + "+"
    lines.append(separator)

    # Header row
    header = "|" + "|".join(f" {col:<{col_widths[col]}} " for col in df.columns) + "|"
    lines.append(header)
    lines.append(separator)

    # Data rows
    for _, row in df.iterrows():
        data_row = "|" + "|".join(f" {str(value):<{col_widths[col]}} " for col, value in zip(df.columns, row)) + "|"
        lines.append(data_row)

    lines.append(separator)
    return "\n".join(lines)

def to_markdown(df: pd.DataFrame) -> str:
    """
    Converts DataFrame to markdown table format.
    """
    if df.empty:
        return ""

    # Build markdown table
    lines = []

    # Header row
    header = "| " + " | ".join(str(col) for col in df.columns) + " |"
    lines.append(header)

    # Separator row
    separator = "| " + " | ".join("---" for _ in df.columns) + " |"
    lines.append(separator)

    # Data rows
    for _, row in df.iterrows():
        data_row = "| " + " | ".join(str(value) for value in row) + " |"
        lines.append(data_row)

    return "\n".join(lines)

def render():
    st.title("Markdown Table Converter")
    st.write("Convert between markdown tables and other formats, or convert Excel-like data to markdown.")

    # Create tabs
    tab1, tab2 = st.tabs(["Markdown → Other Formats", "Excel → Markdown"])

    with tab1:
        st.header("Convert Markdown to Other Formats")
        st.write("Convert markdown tables to formats compatible with Teams, Excel, and Confluence.")

        # Input section
        input_text = st.text_area(
            "Paste your markdown table here:",
            value="| Name | Age | City |\n|------|-----|------|\n| John | 25  | NYC  |\n| Jane | 30  | LA   |",
            height=200,
            help="Paste a markdown table with | separators and header row"
        )

        if st.button("Convert Table", type="primary", key="convert_md"):
            if not input_text.strip():
                st.warning("Please enter a markdown table.")
                return

            # Parse the table
            df = parse_markdown_table(input_text)

            if df.empty:
                st.error("Could not parse the markdown table. Please check the format.")
                return

            st.success(f"Successfully parsed table with {len(df)} rows and {len(df.columns)} columns.")

            # Display the parsed table
            st.subheader("Parsed Table Preview")
            st.dataframe(df, use_container_width=True)

            # Output formats
            st.header("Converted Formats")

            # Teams HTML
            st.subheader("Microsoft Teams (HTML)")
            teams_html = to_teams_html(df)
            st.code(teams_html, language="html")
            st.info("Copy the HTML above and paste it into Teams. It will render as a formatted table.")

            # Excel CSV
            st.subheader("Excel (CSV)")
            excel_csv = to_excel_csv(df)
            st.code(excel_csv, language="text")
            st.info("Copy the CSV above and paste it into Excel, or save as a .csv file.")

            # Confluence HTML
            st.subheader("Confluence (HTML)")
            confluence_html = to_confluence_html(df)
            st.code(confluence_html, language="html")
            st.info("Copy the HTML above and paste it into Confluence in HTML mode.")

            # Plain text
            st.subheader("Plain Text (Formatted)")
            plain_text = to_plain_text(df)
            st.code(plain_text, language="text")
            st.info("Copy the formatted text above for use in plain text applications.")

            # Download options
            st.header("Download Options")

            col1, col2 = st.columns(2)

            with col1:
                # CSV download
                csv_data = excel_csv.encode('utf-8')
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name="table.csv",
                    mime="text/csv"
                )

            with col2:
                # HTML download for Teams
                html_data = teams_html.encode('utf-8')
                st.download_button(
                    label="Download HTML (Teams)",
                    data=html_data,
                    file_name="table_teams.html",
                    mime="text/html"
                )

    with tab2:
        st.header("Convert Excel Data to Markdown")
        st.write("Paste Excel data (tab-separated or space-separated) and convert it to markdown format.")

        # Input section for Excel data
        excel_input = st.text_area(
            "Paste your Excel data here:",
            value="Name\tAge\tCity\nJohn\t25\tNYC\nJane\t30\tLA",
            height=200,
            help="Paste Excel data. It can be tab-separated, space-separated, or copied directly from Excel."
        )

        if st.button("Convert to Markdown", type="primary", key="convert_excel"):
            if not excel_input.strip():
                st.warning("Please enter Excel data.")
                return

            # Parse the Excel data
            df = parse_excel_data(excel_input)

            if df.empty:
                st.error("Could not parse the Excel data. Please check the format.")
                return

            st.success(f"Successfully parsed data with {len(df)} rows and {len(df.columns)} columns.")

            # Display the parsed table
            st.subheader("Parsed Data Preview")
            st.dataframe(df, use_container_width=True)

            # Convert to markdown
            markdown_output = to_markdown(df)

            # Display markdown output
            st.subheader("Markdown Output")
            st.code(markdown_output, language="markdown")
            st.info("Copy the markdown above and paste it into your markdown document.")

            # Download markdown
            st.header("Download Options")
            markdown_data = markdown_output.encode('utf-8')
            st.download_button(
                label="Download Markdown",
                data=markdown_data,
                file_name="table.md",
                mime="text/markdown"
            )

if __name__ == "__main__":
    render()
