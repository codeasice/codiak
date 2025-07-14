import streamlit as st
import pandas as pd
import io

def list_to_table(input_text: str, delimiter: str = None, force_single_column: bool = False) -> str:
    """
    Converts a list or delimited text to a markdown table.
    If force_single_column is True, treat as single column regardless of content.
    Handles inconsistent rows gracefully.
    """
    lines = [line.strip() for line in input_text.strip().splitlines() if line.strip()]
    if not lines:
        return ''
    if force_single_column:
        df = pd.DataFrame(lines, columns=["Item"])
    else:
        # Try to detect delimiter if not provided
        if delimiter is None:
            if any(',' in line for line in lines):
                delimiter = ','
            elif any('\t' in line for line in lines):
                delimiter = '\t'
        if delimiter:
            try:
                # Find max number of columns
                max_cols = max(len(line.split(delimiter)) for line in lines)
                # Pad lines with missing columns
                padded_lines = [
                    delimiter.join(line.split(delimiter) + [''] * (max_cols - len(line.split(delimiter))))
                    for line in lines
                ]
                df = pd.read_csv(io.StringIO('\n'.join(padded_lines)), delimiter=delimiter)
            except Exception:
                st.warning("Malformed input: Could not parse as a table. Falling back to single column.")
                df = pd.DataFrame(lines, columns=["Item"])
        else:
            df = pd.DataFrame(lines, columns=["Item"])
    return df_to_markdown_table(df)

def df_to_markdown_table(df: pd.DataFrame) -> str:
    """
    Converts a pandas DataFrame to a markdown table string.
    """
    return df.to_markdown(index=False)

def parse_markdown_table(md: str) -> pd.DataFrame:
    """
    Parses a markdown table string into a pandas DataFrame.
    """
    try:
        # Remove code block markers if present
        md = md.strip()
        if md.startswith('```'):
            md = '\n'.join(line for line in md.splitlines() if not line.strip().startswith('```'))
        # Pandas can read markdown tables with read_csv if we convert pipes to CSV
        lines = [line for line in md.splitlines() if line.strip() and '|' in line]
        if not lines:
            return pd.DataFrame()
        # Remove separator line (e.g. |---|---|)
        if len(lines) > 1 and set(lines[1].replace('|', '').strip()) <= set('-: '):
            lines.pop(1)
        csv_lines = [','.join(cell.strip() for cell in line.strip('|').split('|')) for line in lines]
        df = pd.read_csv(io.StringIO('\n'.join(csv_lines)))
        return df
    except Exception:
        return pd.DataFrame()

def join_tables(md1: str, md2: str, how: str = 'append') -> str:
    """
    Joins two markdown tables. If 'append', rows are appended. If 'align', columns are aligned by header.
    """
    df1 = parse_markdown_table(md1)
    df2 = parse_markdown_table(md2)
    if df1.empty:
        return df_to_markdown_table(df2)
    if df2.empty:
        return df_to_markdown_table(df1)
    if how == 'append':
        # If columns match, just append
        if list(df1.columns) == list(df2.columns):
            df = pd.concat([df1, df2], ignore_index=True)
        else:
            # Outer join on columns
            df = pd.concat([df1, df2], ignore_index=True, sort=False)
    elif how == 'align':
        # Outer join on columns, fill missing with blank
        df = pd.concat([df1, df2], ignore_index=True, sort=False)
    else:
        return 'Invalid join type.'
    return df_to_markdown_table(df)

def render():
    st.write("Create a markdown table from a list or join two tables.")
    st.info("Paste a list (one item per line), CSV/TSV, or two markdown tables to join.")

    st.header("Create Table from List")
    input_list = st.text_area("List or CSV/TSV Input:", value="Apple\nBanana\nCherry", height=120, key="table_creator_list")
    delimiter = st.selectbox("Delimiter (for multi-column)", ["Auto", ", (comma)", "\t (tab)", "None (single column)"], index=0, key="table_creator_delim")
    if delimiter == "Auto":
        delim_val = None
        force_single_column = False
    elif delimiter == ", (comma)":
        delim_val = ","
        force_single_column = False
    elif delimiter == "\t (tab)":
        delim_val = "\t"
        force_single_column = False
    else:
        delim_val = None
        force_single_column = True
    if st.button("Create Table", key="create_table_btn"):
        table_md = list_to_table(input_list, delimiter=delim_val, force_single_column=force_single_column)
        st.text_area("Markdown Table Output:", value=table_md, height=150, key="table_creator_table_out")

    st.header("Join Two Tables")
    table1 = st.text_area("Table 1 (Markdown):", value="| Fruit | Color |\n|-------|-------|\n| Apple | Red   |", height=100, key="table_creator_table1")
    table2 = st.text_area("Table 2 (Markdown):", value="| Fruit | Color |\n|-------|-------|\n| Banana| Yellow|", height=100, key="table_creator_table2")
    join_type = st.selectbox("Join Type", ["Append Rows (default)", "Align Columns (outer join)"])
    if st.button("Join Tables", key="join_tables_btn"):
        how = 'append' if join_type.startswith("Append") else 'align'
        joined_md = join_tables(table1, table2, how=how)
        st.text_area("Joined Markdown Table:", value=joined_md, height=150, key="table_creator_joined_out")