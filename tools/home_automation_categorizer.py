import streamlit as st

def render():
    suffix_categories = {
        '_battery': 'Battery',
        '_motion': 'Motion',
        '_temperature': 'Temperature',
        '_wi_fi_signal_strength': 'Wi-Fi Signal Strength',
        '_camera_motion_detection': 'Camera Motion Detection',
    }
    # Text area for user input
    user_input = st.text_area(
        "Paste your list (one item per line):",
        height=200,
        placeholder="device1_battery\ndevice2_motion\ndevice3_temperature\n..."
    )
    if not user_input.strip():
        st.info("Enter your list above to see categorized results.")
        return
    # Split and categorize
    lines = [line for line in user_input.splitlines() if line.strip()]
    categorized = {cat: [] for cat in suffix_categories.values()}
    uncategorized = []
    for line in lines:
        matched = False
        for suffix, cat in suffix_categories.items():
            if line.endswith(suffix):
                categorized[cat].append(line)
                matched = True
                break
        if not matched:
            uncategorized.append(line)
    # Display results
    for cat, items in categorized.items():
        if items:
            st.subheader(f"{cat} ({len(items)})")
            st.code("\n".join(items), language="text")
    if uncategorized:
        st.subheader(f"Uncategorized ({len(uncategorized)})")
        st.code("\n".join(uncategorized), language="text")