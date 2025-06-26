import streamlit as st
import requests
import os
import pandas as pd
import time
import json
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import pytz

def render():
    # API/Token input
    default_api_url = os.getenv("SMARTTHINGS_API_URL", "https://api.smartthings.com")
    default_token = os.getenv("SMARTTHINGS_TOKEN", "")
    with st.expander("API/Token Settings", expanded=False):
        api_url = st.text_input("SmartThings API URL", value=default_api_url, help="e.g. https://api.smartthings.com")
        token = st.text_input("Personal Access Token", value=default_token, type="password")

    if not api_url or not token:
        st.error("Please provide both the API URL and token, or set them in your .env file as SMARTTHINGS_API_URL and SMARTTHINGS_TOKEN.")
        st.stop()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    endpoint = f"{api_url.rstrip('/')}/v1/devices"

    # Fetch devices on page load
    with st.spinner("Fetching devices from SmartThings..."):
        try:
            resp = requests.get(endpoint, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            devices = data.get('items', [])
        except requests.RequestException as e:
            st.error(f"Error connecting to SmartThings: {e}")
            return

    # Group devices by category
    def get_category(d):
        try:
            comps = d.get('components', [])
            if comps and 'categories' in comps[0] and comps[0]['categories']:
                name = comps[0]['categories'][0].get('name', '').lower()
                if 'garage' in name:
                    return 'Garage Door'
                elif 'lock' in name:
                    return 'SmartLock'
                elif 'motion' in name:
                    return 'Motion Sensors'
                elif 'light' in name:
                    return 'Lights'
                elif 'switch' in name or 'plug' in name:
                    return 'Switches'
                else:
                    return 'Other'
        except Exception:
            pass
        return 'Other'

    sections = {
        'Motion Sensors': [],
        'Lights': [],
        'Switches': [],
        'Garage Door': [],
        'SmartLock': [],
        'Other': []
    }
    for d in devices:
        cat = get_category(d)
        sections[cat].append(d)

    # Session state for statuses and raw data
    if 'st_dashboard_statuses' not in st.session_state:
        st.session_state['st_dashboard_statuses'] = {}
    if 'st_dashboard_raw_status' not in st.session_state:
        st.session_state['st_dashboard_raw_status'] = {}

    def fetch_statuses(devices, section_key):
        start_time = time.time()
        statuses = {}
        raw_status_data = {}
        progress_bar = st.progress(0, text=f"Fetching {section_key} statuses...")
        total = len(devices)
        lock = threading.Lock()

        def fetch_one(idx, d):
            device_id = d.get('deviceId', '')
            status = 'Unavailable'
            local_raw = None
            if device_id:
                status_endpoint = f"{api_url.rstrip('/')}/v1/devices/{device_id}/status"
                try:
                    status_resp = requests.get(status_endpoint, headers=headers, timeout=10)
                    status_resp.raise_for_status()
                    status_data = status_resp.json()
                    local_raw = status_data
                    # Try to get a summary of the main component's status
                    if 'components' in status_data and 'main' in status_data['components']:
                        main_status = status_data['components']['main']
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
            return idx, device_id, status, local_raw

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fetch_one, idx, d) for idx, d in enumerate(devices)]
            for i, future in enumerate(as_completed(futures)):
                idx, device_id, status, local_raw = future.result()
                with lock:
                    statuses[device_id] = status
                    if device_id and local_raw:
                        raw_status_data[device_id] = local_raw
                    progress_bar.progress((i + 1) / total, text=f"Fetching {section_key} statuses... ({i + 1}/{total})")
        progress_bar.empty()
        elapsed = time.time() - start_time
        st.session_state['st_dashboard_statuses'][section_key] = statuses
        st.session_state['st_dashboard_raw_status'][section_key] = raw_status_data
        # Store last fetched time (UTC)
        st.session_state[f'st_dashboard_last_fetched_{section_key}'] = time.time()
        return elapsed

    # Render each section
    # First, build a list of sections to render, with 'Other' last
    section_order = [s for s in sections.keys() if s not in ("Garage Door", "SmartLock", "Other")]
    # Security section will be rendered separately
    section_order.append("Security")
    section_order.append("Other")

    for section in section_order:
        if section == "Security":
            # --- Security Section: Garage Door and SmartLock ---
            security_devices = [d for d in devices if get_category(d) in ("Garage Door", "SmartLock")]
            if security_devices:
                st.subheader('Security')
                col1, col2 = st.columns([1, 3])
                section_key = 'Security'
                # Fetch button
                with col1:
                    if st.button(f"Fetch Security Statuses", key=f"fetch_{section_key}"):
                        elapsed = fetch_statuses(security_devices, section_key)
                        st.session_state['st_dashboard_statuses'][section_key] = st.session_state['st_dashboard_statuses'][section_key]
                        st.session_state['st_dashboard_raw_status'][section_key] = st.session_state['st_dashboard_raw_status'][section_key]
                        st.rerun()
                # Show cards
                with col2:
                    garage_doors = [d for d in security_devices if get_category(d) == 'Garage Door']
                    smart_locks = [d for d in security_devices if get_category(d) == 'SmartLock']
                    if garage_doors:
                        st.markdown('**Garage Doors**')
                        cols = st.columns(len(garage_doors))
                        raw_statuses = st.session_state['st_dashboard_raw_status'].get(section_key, {})
                        for idx, d in enumerate(garage_doors):
                            with cols[idx]:
                                label = d.get('label') or d.get('name') or 'Garage Door'
                                device_id = d.get('deviceId', '')
                                status = 'Unknown'
                                if device_id and device_id in raw_statuses:
                                    try:
                                        # Try garageDoorControl first, then doorControl
                                        main = raw_statuses[device_id]['components']['main']
                                        door = main.get('garageDoorControl', {})
                                        if 'door' in door:
                                            status = door['door']['value']
                                        else:
                                            door = main.get('doorControl', {})
                                            if 'door' in door:
                                                status = door['door']['value']
                                    except Exception:
                                        status = 'Unknown'
                                st.markdown(f"**{label}**")
                                st.markdown(f"Status: `{status}`")
                    if smart_locks:
                        st.markdown('**Smart Locks**')
                        cols = st.columns(len(smart_locks))
                        raw_statuses = st.session_state['st_dashboard_raw_status'].get(section_key, {})
                        for idx, d in enumerate(smart_locks):
                            with cols[idx]:
                                label = d.get('label') or d.get('name') or 'Smart Lock'
                                device_id = d.get('deviceId', '')
                                status = 'Unknown'
                                if device_id and device_id in raw_statuses:
                                    try:
                                        lock = raw_statuses[device_id]['components']['main'].get('lock', {})
                                        if 'lock' in lock:
                                            status = lock['lock']['value']
                                    except Exception:
                                        status = 'Unknown'
                                st.markdown(f"**{label}**")
                                st.markdown(f"Status: `{status}`")
                # Show raw status JSON for Security section
                if section_key in st.session_state['st_dashboard_raw_status'] and st.session_state['st_dashboard_raw_status'][section_key]:
                    with st.expander("Show Security status JSON", expanded=False):
                        st.code(json.dumps(st.session_state['st_dashboard_raw_status'][section_key], indent=2), language="json")
            continue  # Skip to next section
        # Skip Garage Door and SmartLock in the main table rendering
        if section in ("Garage Door", "SmartLock"):
            continue
        devs = sections.get(section, [])
        if section in ["Lights", "Switches"]:
            st.subheader(f"{section} ({len(devs)})")
            # Fetch button below header
            if st.button(f"Fetch {section} Statuses", key=f"fetch_{section}"):
                elapsed = fetch_statuses(devs, section)
                st.session_state['st_dashboard_statuses'][section] = st.session_state['st_dashboard_statuses'][section]
                st.session_state['st_dashboard_raw_status'][section] = st.session_state['st_dashboard_raw_status'][section]
                st.rerun()
            # Render toggles always visible
            if not devs:
                st.info(f"No devices found in {section}.")
                continue
            statuses = st.session_state['st_dashboard_statuses'].get(section, {})
            online_status_map = {}
            for d in devs:
                device_id = d.get('deviceId', '')
                online = 'Unknown'
                if device_id:
                    try:
                        health_endpoint = f"{api_url.rstrip('/')}/v1/devices/{device_id}/health"
                        health_resp = requests.get(health_endpoint, headers=headers, timeout=5)
                        health_resp.raise_for_status()
                        health_data = health_resp.json()
                        state = health_data.get('state', '').lower()
                        if state == 'online':
                            online = '✅'
                        elif state == 'offline':
                            online = '❌'
                        else:
                            online = state
                    except Exception:
                        online = '❓'
                online_status_map[device_id] = online
                status = statuses.get(device_id, '')
                is_on = False
                if 'switch: on' in status:
                    is_on = True
                elif 'switch: off' in status:
                    is_on = False
                toggle_key = f'{section.lower()}_toggle_{device_id}'
                pending_key = f'{section.lower()}_toggle_pending_{device_id}'
                label = d.get('label') or d.get('name') or section[:-1]
                toggle_label = f"{online_status_map[device_id]} {label}"
                toggled = st.toggle(toggle_label, value=is_on, key=toggle_key)
                if toggled != is_on and not st.session_state.get(pending_key, False):
                    api_url = st.session_state.get('SMARTTHINGS_API_URL', os.getenv('SMARTTHINGS_API_URL', 'https://api.smartthings.com'))
                    token = st.session_state.get('SMARTTHINGS_TOKEN', os.getenv('SMARTTHINGS_TOKEN', ''))
                    headers = {
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    }
                    command = 'on' if toggled else 'off'
                    command_body = {
                        "commands": [
                            {
                                "component": "main",
                                "capability": "switch",
                                "command": command
                            }
                        ]
                    }
                    endpoint = f"{api_url.rstrip('/')}/v1/devices/{device_id}/commands"
                    try:
                        resp = requests.post(endpoint, headers=headers, data=json.dumps(command_body), timeout=10)
                        resp.raise_for_status()
                        st.session_state[pending_key] = True
                        st.success(f"Sent '{command}' command to {section[:-1].lower()}.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to send command: {e}")
                elif toggled == is_on and st.session_state.get(pending_key, False):
                    st.session_state[pending_key] = False
            # Table in expander
            with st.expander(f"{section} Table ({len(devs)})", expanded=False):
                table = []
                for d in devs:
                    row = {
                        'Name': d.get('name', ''),
                        'Label': d.get('label', ''),
                        'Type': d.get('type', ''),
                        'Status': statuses.get(d.get('deviceId', ''), ''),
                    }
                    if section == 'Lights':
                        caps = []
                        try:
                            comps = d.get('components', [])
                            if comps and 'capabilities' in comps[0]:
                                caps = [c.get('id', '') for c in comps[0]['capabilities']]
                        except Exception:
                            pass
                        row['Color Type'] = 'Color' if 'colorControl' in caps else 'White'
                    table.append(row)
                df = pd.DataFrame(table)
                if not df.empty:
                    st.dataframe(df, use_container_width=True, hide_index=True)
        elif section == "Other":
            st.subheader(f"Other ({len(devs)})")
            with st.expander(f"{section} ({len(devs)})", expanded=False):
                if not devs:
                    st.info(f"No devices found in {section}.")
                    continue
                table = []
                statuses = st.session_state['st_dashboard_statuses'].get(section, {})
                for d in devs:
                    row = {
                        'Name': d.get('name', ''),
                        'Label': d.get('label', ''),
                        'Type': d.get('type', ''),
                        'Status': statuses.get(d.get('deviceId', ''), ''),
                    }
                    category = 'Unknown'
                    try:
                        comps = d.get('components', [])
                        if comps and 'categories' in comps[0] and comps[0]['categories']:
                            category = comps[0]['categories'][0].get('name', 'Unknown')
                    except Exception:
                        category = 'Unknown'
                    row['Category'] = category
                    table.append(row)
                df = pd.DataFrame(table)
                if not df.empty:
                    st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            if section == 'Motion Sensors':
                st.subheader(f"{section} ({len(devs)})")
                # Fetch button below header
                if st.button(f"Fetch {section} Statuses", key=f"fetch_{section}"):
                    elapsed = fetch_statuses(devs, section)
                    st.session_state['st_dashboard_statuses'][section] = st.session_state['st_dashboard_statuses'][section]
                    st.session_state['st_dashboard_raw_status'][section] = st.session_state['st_dashboard_raw_status'][section]
                    st.rerun()
                if not devs:
                    st.info(f"No devices found in {section}.")
                    continue
                statuses = st.session_state['st_dashboard_statuses'].get(section, {})
                raw_statuses = st.session_state['st_dashboard_raw_status'].get(section, {})
                table = []
                now = time.time()
                for d in devs:
                    device_id = d.get('deviceId', '')
                    label = d.get('label', '') or d.get('name', '')
                    row = {'Name': d.get('name', ''), 'Label': label}
                    # Defaults
                    motion = battery = temp = motion_ts = battery_ts = temp_ts = None
                    motion_ago = ''
                    motion_ts_epoch = 0
                    motion_ts_est = ''
                    # Parse raw status
                    if device_id in raw_statuses:
                        main = raw_statuses[device_id].get('components', {}).get('main', {})
                        # Motion
                        motion_val = main.get('motionSensor', {}).get('motion', {})
                        if 'value' in motion_val:
                            motion = motion_val['value']
                            motion_ts = motion_val.get('timestamp')
                            if motion_ts:
                                try:
                                    dt = datetime.fromisoformat(motion_ts.replace('Z', '+00:00'))
                                    motion_ts_epoch = dt.replace(tzinfo=timezone.utc).timestamp()
                                    ago = time.time() - motion_ts_epoch
                                    if ago < 60:
                                        motion_ago = f"{int(ago)}s ago"
                                    elif ago < 3600:
                                        motion_ago = f"{int(ago//60)}m ago"
                                    elif ago < 86400:
                                        motion_ago = f"{int(ago//3600)}h ago"
                                    else:
                                        motion_ago = f"{int(ago//86400)}d ago"
                                    # EST timestamp
                                    est = dt.astimezone(pytz.timezone('US/Eastern'))
                                    motion_ts_est = est.strftime('%Y-%m-%d %I:%M:%S %p %Z')
                                except Exception:
                                    motion_ago = ''
                                    motion_ts_est = ''
                        # Battery
                        battery_val = main.get('battery', {}).get('battery', {})
                        if 'value' in battery_val:
                            battery = battery_val['value']
                            battery_ts = battery_val.get('timestamp')
                        # Temperature
                        temp_val = main.get('temperatureMeasurement', {}).get('temperature', {})
                        if 'value' in temp_val:
                            temp = temp_val['value']
                            temp_ts = temp_val.get('timestamp')
                    # Format columns
                    row['Motion'] = ("🚶‍♂️ Active" if motion == 'active' else "💤 Inactive") if motion else 'Unknown'
                    row['Timestamp (EST)'] = motion_ts_est
                    row['Motion Time'] = motion_ago
                    row['Battery'] = f"{battery}%" if battery is not None else ''
                    row['Temperature'] = f"{round(temp,1)}°F" if temp is not None else ''
                    row['_motion_ts_epoch'] = motion_ts_epoch
                    table.append(row)
                df = pd.DataFrame(table)
                if not df.empty:
                    df = df.sort_values(by='_motion_ts_epoch', ascending=False).drop(columns=['_motion_ts_epoch'])
                    st.dataframe(df, use_container_width=True, hide_index=True)
                continue
            st.subheader(f"{section} ({len(devs)})")
            if not devs:
                st.info(f"No devices found in {section}.")
                continue
            # Build table
            table = []
            statuses = st.session_state['st_dashboard_statuses'].get(section, {})
            for d in devs:
                row = {
                    'Name': d.get('name', ''),
                    'Label': d.get('label', ''),
                    'Type': d.get('type', ''),
                    'Status': statuses.get(d.get('deviceId', ''), ''),
                }
                if section == 'Other':
                    category = 'Unknown'
                    try:
                        comps = d.get('components', [])
                        if comps and 'categories' in comps[0] and comps[0]['categories']:
                            category = comps[0]['categories'][0].get('name', 'Unknown')
                    except Exception:
                        category = 'Unknown'
                    row['Category'] = category
                table.append(row)
            df = pd.DataFrame(table)
            if section == 'Lights' and not df.empty:
                color_types = []
                toggles = []
                online_status_map = {}
                for d in devs:
                    caps = []
                    try:
                        comps = d.get('components', [])
                        if comps and 'capabilities' in comps[0]:
                            caps = [c.get('id', '') for c in comps[0]['capabilities']]
                    except Exception:
                        pass
                    color_types.append('Color' if 'colorControl' in caps else 'White')
                    device_id = d.get('deviceId', '')
                    online = 'Unknown'
                    if device_id:
                        try:
                            health_endpoint = f"{api_url.rstrip('/')}/v1/devices/{device_id}/health"
                            health_resp = requests.get(health_endpoint, headers=headers, timeout=5)
                            health_resp.raise_for_status()
                            health_data = health_resp.json()
                            state = health_data.get('state', '').lower()
                            if state == 'online':
                                online = '✅'
                            elif state == 'offline':
                                online = '❌'
                            else:
                                online = state
                        except Exception:
                            online = '❓'
                    online_status_map[device_id] = online
                    status = st.session_state['st_dashboard_statuses'].get(section, {}).get(device_id, '')
                    is_on = False
                    if 'switch: on' in status:
                        is_on = True
                    elif 'switch: off' in status:
                        is_on = False
                    toggle_key = f'light_toggle_{device_id}'
                    pending_key = f'light_toggle_pending_{device_id}'
                    light_label = d.get('label') or d.get('name') or 'Light'
                    toggle_label = f"{online_status_map[device_id]} {light_label}"
                    toggled = st.toggle(toggle_label, value=is_on, key=toggle_key)
                    if toggled != is_on and not st.session_state.get(pending_key, False):
                        api_url = st.session_state.get('SMARTTHINGS_API_URL', os.getenv('SMARTTHINGS_API_URL', 'https://api.smartthings.com'))
                        token = st.session_state.get('SMARTTHINGS_TOKEN', os.getenv('SMARTTHINGS_TOKEN', ''))
                        headers = {
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json",
                        }
                        command = 'on' if toggled else 'off'
                        command_body = {
                            "commands": [
                                {
                                    "component": "main",
                                    "capability": "switch",
                                    "command": command
                                }
                            ]
                        }
                        endpoint = f"{api_url.rstrip('/')}/v1/devices/{device_id}/commands"
                        try:
                            resp = requests.post(endpoint, headers=headers, data=json.dumps(command_body), timeout=10)
                            resp.raise_for_status()
                            st.session_state[pending_key] = True
                            st.success(f"Sent '{command}' command to light.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to send command: {e}")
                    elif toggled == is_on and st.session_state.get(pending_key, False):
                        st.session_state[pending_key] = False
                df['Color Type'] = color_types
                if 'Online' in df.columns:
                    df = df.drop(columns=['Online'])
                cols = [c for c in df.columns if c != 'Color Type'] + ['Color Type']
                df = df[cols]
                st.dataframe(df, use_container_width=True, hide_index=True)
            elif section == 'Switches' and not df.empty:
                toggles = []
                online_status_map = {}
                for d in devs:
                    device_id = d.get('deviceId', '')
                    online = 'Unknown'
                    if device_id:
                        try:
                            health_endpoint = f"{api_url.rstrip('/')}/v1/devices/{device_id}/health"
                            health_resp = requests.get(health_endpoint, headers=headers, timeout=5)
                            health_resp.raise_for_status()
                            health_data = health_resp.json()
                            state = health_data.get('state', '').lower()
                            if state == 'online':
                                online = '✅'
                            elif state == 'offline':
                                online = '❌'
                            else:
                                online = state
                        except Exception:
                            online = '❓'
                    online_status_map[device_id] = online
                    status = st.session_state['st_dashboard_statuses'].get(section, {}).get(device_id, '')
                    is_on = False
                    if 'switch: on' in status:
                        is_on = True
                    elif 'switch: off' in status:
                        is_on = False
                    toggle_key = f'switch_toggle_{device_id}'
                    pending_key = f'switch_toggle_pending_{device_id}'
                    switch_label = d.get('label') or d.get('name') or 'Switch'
                    toggle_label = f"{online_status_map[device_id]} {switch_label}"
                    toggled = st.toggle(toggle_label, value=is_on, key=toggle_key)
                    if toggled != is_on and not st.session_state.get(pending_key, False):
                        api_url = st.session_state.get('SMARTTHINGS_API_URL', os.getenv('SMARTTHINGS_API_URL', 'https://api.smartthings.com'))
                        token = st.session_state.get('SMARTTHINGS_TOKEN', os.getenv('SMARTTHINGS_TOKEN', ''))
                        headers = {
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json",
                        }
                        command = 'on' if toggled else 'off'
                        command_body = {
                            "commands": [
                                {
                                    "component": "main",
                                    "capability": "switch",
                                    "command": command
                                }
                            ]
                        }
                        endpoint = f"{api_url.rstrip('/')}/v1/devices/{device_id}/commands"
                        try:
                            resp = requests.post(endpoint, headers=headers, data=json.dumps(command_body), timeout=10)
                            resp.raise_for_status()
                            st.session_state[pending_key] = True
                            st.success(f"Sent '{command}' command to switch.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to send command: {e}")
                    elif toggled == is_on and st.session_state.get(pending_key, False):
                        st.session_state[pending_key] = False
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)
        col1, col2 = st.columns([1, 3])
        with col1:
            # Show fetch message for a few seconds only for Motion Sensors and not auto-refresh
            if section == 'Motion Sensors' and not st.session_state.get('motion_auto_refresh', False):
                msg = st.session_state.get('last_fetch_msg', None)
                t = st.session_state.get('last_fetch_time', 0)
                import time as _time
                if msg and _time.time() - t < 3:
                    st.success(msg)
                elif msg:
                    st.session_state['last_fetch_msg'] = None
                    st.session_state['last_fetch_time'] = 0
        # Show raw status JSON for this section if available
        if section in st.session_state['st_dashboard_raw_status'] and st.session_state['st_dashboard_raw_status'][section]:
            with st.expander("Show raw status JSON", expanded=False):
                st.code(json.dumps(st.session_state['st_dashboard_raw_status'][section], indent=2), language="json")

    # Show raw data
    with st.expander("Show raw API data", expanded=False):
        st.code(json.dumps({
            'devices': data,
            'statuses': st.session_state['st_dashboard_raw_status']
        }, indent=2), language="json")