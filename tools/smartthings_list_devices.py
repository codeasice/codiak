import streamlit as st
import requests
import os
import pandas as pd
import time

def render():
    st.header("SmartThings Devices")
    st.write("Connect to your SmartThings account and list all devices.")

    # Try to load from environment variables
    default_api_url = os.getenv("SMARTTHINGS_API_URL", "https://api.smartthings.com")
    default_token = os.getenv("SMARTTHINGS_TOKEN", "")

    with st.expander("API/Token Settings", expanded=False):
        api_url = st.text_input("SmartThings API URL", value=default_api_url, help="e.g. https://api.smartthings.com")
        token = st.text_input("Personal Access Token", value=default_token, type="password")

    if st.button("Fetch Devices"):
        if not api_url or not token:
            st.error("Please provide both the API URL and token, or set them in your .env file as SMARTTHINGS_API_URL and SMARTTHINGS_TOKEN.")
            st.stop()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        endpoint = f"{api_url.rstrip('/')}/v1/devices"
        try:
            with st.spinner("Fetching devices from SmartThings..."):
                resp = requests.get(endpoint, headers=headers, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                devices = data.get('items', [])

                if not devices:
                    st.info("No devices found.")
                    return

                import json
                start_time = time.time()
                table = []
                raw_status_data = {}
                progress_bar = st.progress(0, text="Fetching device statuses...")
                total_devices = len(devices)
                for idx, d in enumerate(devices):
                    device_id = d.get('deviceId', '')
                    status = 'Unavailable'
                    # Extract category name
                    category = 'Unknown'
                    try:
                        comps = d.get('components', [])
                        if comps and 'categories' in comps[0] and comps[0]['categories']:
                            category = comps[0]['categories'][0].get('name', 'Unknown')
                    except Exception:
                        category = 'Unknown'
                    if device_id:
                        status_endpoint = f"{api_url.rstrip('/')}/v1/devices/{device_id}/status"
                        try:
                            status_resp = requests.get(status_endpoint, headers=headers, timeout=10)
                            status_resp.raise_for_status()
                            status_data = status_resp.json()
                            raw_status_data[device_id] = status_data
                            # Try to get a summary of the main component's status
                            if 'components' in status_data and 'main' in status_data['components']:
                                main_status = status_data['components']['main']
                                # Get a summary of all capability states
                                cap_states = []
                                for cap, val in main_status.items():
                                    if isinstance(val, dict) and 'value' in val:
                                        cap_states.append(f"{cap}: {val['value']}")
                                    elif isinstance(val, dict):
                                        for k, v in val.items():
                                            if isinstance(v, dict) and 'value' in v:
                                                cap_states.append(f"{cap}.{k}: {v['value']}")
                                status = ", ".join(cap_states) if cap_states else 'OK'
                        except Exception:
                            status = 'Unavailable'
                    table.append({
                        'Device ID': device_id,
                        'Name': d.get('name', ''),
                        'Label': d.get('label', ''),
                        'Manufacturer': d.get('manufacturerName', ''),
                        'Type': d.get('type', ''),
                        'Category': category,
                        'Location': d.get('locationId', ''),
                        'Status': status,
                    })
                    progress_bar.progress((idx + 1) / total_devices, text=f"Fetching device statuses... ({idx + 1}/{total_devices})")
                progress_bar.empty()
                elapsed = time.time() - start_time
                df = pd.DataFrame(table)
                st.success(f"Found {len(df)} devices.")
                st.dataframe(df, use_container_width=True)
                st.write(f"⏱️ Total fetch time: {elapsed:.2f} seconds")
                with st.expander("Show raw API data", expanded=False):
                    st.code(json.dumps({
                        'devices': data,
                        'statuses': raw_status_data
                    }, indent=2), language="json")
        except requests.RequestException as e:
            st.error(f"Error connecting to SmartThings: {e}")