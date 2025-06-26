import streamlit as st
import requests
import os
import pandas as pd

def render():
    st.header("Home Assistant Sensors")
    st.write("Connect to your Home Assistant instance and list all sensors.")

    # Try to load from environment variables
    default_api_url = os.getenv("HOME_ASSISTANT_API_URL", "")
    default_token = os.getenv("HOME_ASSISTANT_TOKEN", "")

    api_url = st.text_input("Home Assistant API URL", value=default_api_url, help="e.g. http://localhost:8123/api")
    token = st.text_input("Long-Lived Access Token", value=default_token, type="password")

    entity_filter = st.text_input("Filter by Entity ID (substring)", "")
    device_class_filter = st.text_input("Filter by Device Class (exact)", "")

    if st.button("Fetch Sensors"):
        if not api_url or not token:
            st.error("Please provide both the API URL and token, or set them in your .env file as HOME_ASSISTANT_API_URL and HOME_ASSISTANT_TOKEN.")
            st.stop()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        endpoint = f"{api_url.rstrip('/')}/states"
        try:
            with st.spinner("Fetching sensors from Home Assistant..."):
                resp = requests.get(endpoint, headers=headers, timeout=10)
                resp.raise_for_status()
                entities = resp.json()
                sensors = [e for e in entities if e.get('entity_id', '').startswith('sensor.')]

                # Filtering
                if entity_filter:
                    sensors = [s for s in sensors if entity_filter.lower() in s['entity_id'].lower()]
                if device_class_filter:
                    sensors = [s for s in sensors if s.get('attributes', {}).get('device_class', '') == device_class_filter]

                if not sensors:
                    st.info("No sensors found with the given filters.")
                    return

                # Prepare table data
                table = []
                for s in sensors:
                    attrs = s.get('attributes', {})
                    table.append({
                        'Entity ID': s.get('entity_id', ''),
                        'Friendly Name': attrs.get('friendly_name', ''),
                        'State': s.get('state', ''),
                        'Unit': attrs.get('unit_of_measurement', ''),
                        'Device Class': attrs.get('device_class', ''),
                        'Last Changed': s.get('last_changed', ''),
                    })
                df = pd.DataFrame(table)
                st.success(f"Found {len(df)} sensors.")
                st.dataframe(df, use_container_width=True)
        except requests.RequestException as e:
            st.error(f"Error connecting to Home Assistant: {e}")