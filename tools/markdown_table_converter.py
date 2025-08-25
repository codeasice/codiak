#!/usr/bin/env python3
"""
Markdown Table Converter Tool

Converts markdown tables to formats compatible with:
- Microsoft Teams (HTML table)
- Excel (CSV format)
- Confluence (HTML table)
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

def render():
    st.title("Markdown Table Converter")
    st.write("Convert markdown tables to formats compatible with Teams, Excel, and Confluence.")

    # Input section
    st.header("Input Markdown Table")
    input_text = st.text_area(
        "Paste your markdown table here:",
        value="| Name | Age | City |\n|------|-----|------|\n| John | 25  | NYC  |\n| Jane | 30  | LA   |",
        height=200,
        help="Paste a markdown table with | separators and header row"
    )

    if st.button("Convert Table", type="primary"):
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

if __name__ == "__main__":
    render()
