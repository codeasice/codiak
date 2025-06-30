import streamlit as st
import requests
import os
import pandas as pd
import json
from datetime import datetime, timezone
import pytz

def render():
    st.header("Home Assistant Dashboard")
    st.write("Connect to your Home Assistant instance and control your devices.")

    # API/Token input
    default_api_url = os.getenv("HOME_ASSISTANT_API_URL", "")
    default_token = os.getenv("HOME_ASSISTANT_TOKEN", "")
    with st.expander("API/Token Settings", expanded=False):
        api_url = st.text_input("Home Assistant API URL", value=default_api_url, help="e.g. http://localhost:8123/api")
        token = st.text_input("Long-Lived Access Token", value=default_token, type="password")

    if not api_url or not token:
        st.error("Please provide both the API URL and token, or set them in your .env file as HOME_ASSISTANT_API_URL and HOME_ASSISTANT_TOKEN.")
        st.stop()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    endpoint = f"{api_url.rstrip('/')}/states"

    # Fetch entities
    with st.spinner("Fetching entities from Home Assistant..."):
        try:
            resp = requests.get(endpoint, headers=headers, timeout=10)
            resp.raise_for_status()
            entities = resp.json()
        except requests.RequestException as e:
            st.error(f"Error connecting to Home Assistant: {e}")
            return

    # Group entities by type
    groups = {
        'Motion Sensors': [],
        'Lights': [],
        'Switches': [],
        'Garage Door': [],
        'SmartLock': [],
        'Other': [],
    }
    for e in entities:
        eid = e.get('entity_id', '')
        domain = eid.split('.')[0] if '.' in eid else ''
        attrs = e.get('attributes', {})
        device_class = attrs.get('device_class', '')
        if domain == 'binary_sensor' and device_class == 'motion':
            groups['Motion Sensors'].append(e)
        elif domain == 'light':
            groups['Lights'].append(e)
        elif domain == 'switch':
            groups['Switches'].append(e)
        elif domain == 'lock':
            groups['SmartLock'].append(e)
        elif domain == 'cover' and device_class == 'garage':
            groups['Garage Door'].append(e)
        else:
            groups['Other'].append(e)

    # Session state for toggles and fetched data
    if 'ha_dashboard_toggle_pending' not in st.session_state:
        st.session_state['ha_dashboard_toggle_pending'] = {}
    if 'ha_dashboard_fetched' not in st.session_state:
        st.session_state['ha_dashboard_fetched'] = {}
    if 'ha_dashboard_entities' not in st.session_state:
        st.session_state['ha_dashboard_entities'] = {}

    section_order = ['Motion Sensors', 'Lights', 'Switches', 'Security', 'Other']
    for section in section_order:
        fetch_key = f'ha_fetch_{section.replace(" ", "_").lower()}'
        if section == 'Security':
            security_entities = groups['Garage Door'] + groups['SmartLock']
            if security_entities:
                st.subheader('Security')
                if st.button('Fetch Security Statuses', key=fetch_key):
                    st.session_state['ha_dashboard_fetched'][section] = True
                    st.session_state['ha_dashboard_entities'][section] = security_entities
                    st.rerun()
                if st.session_state['ha_dashboard_fetched'].get(section):
                    with st.expander("Show Security Entities", expanded=False):
                        st.code(json.dumps(st.session_state['ha_dashboard_entities'][section], indent=2), language="json")
                    for e in st.session_state['ha_dashboard_entities'][section]:
                        eid = e.get('entity_id', '')
                        name = e.get('attributes', {}).get('friendly_name', eid)
                        state = e.get('state', 'unknown')
                        st.markdown(f"**{name}**  ")
                        st.markdown(f"Status: `{state}`")
            continue
        devs = groups.get(section, [])
        if not devs:
            continue
        st.subheader(f"{section} ({len(devs)})")
        if st.button(f"Fetch {section} Statuses", key=fetch_key):
            st.session_state['ha_dashboard_fetched'][section] = True
            st.session_state['ha_dashboard_entities'][section] = devs
            st.rerun()
        if not st.session_state['ha_dashboard_fetched'].get(section):
            continue
        devs = st.session_state['ha_dashboard_entities'][section]
        if section in ['Lights', 'Switches']:
            for e in devs:
                eid = e.get('entity_id', '')
                name = e.get('attributes', {}).get('friendly_name', eid)
                state = e.get('state', 'off')
                is_on = state == 'on'
                attrs = e.get('attributes', {})
                available = attrs.get('available', None)
                assumed_state = attrs.get('assumed_state', None)
                # Improved online/available status logic
                if state == 'unavailable':
                    online_status = '❌'
                elif state == 'unknown':
                    online_status = '❓'
                elif available is True:
                    online_status = '✅'
                elif available is False:
                    online_status = '❌'
                elif assumed_state is not None:
                    online_status = '✅' if not assumed_state else '❓'
                else:
                    online_status = '✅'
                toggle_key = f'ha_toggle_{eid}'
                pending_key = f'ha_toggle_pending_{eid}'
                toggle_label = f"{online_status} {name}"
                toggled = st.toggle(toggle_label, value=is_on, key=toggle_key)
                if toggled != is_on and not st.session_state['ha_dashboard_toggle_pending'].get(pending_key, False):
                    service_domain = 'light' if section == 'Lights' else 'switch'
                    service = 'turn_on' if toggled else 'turn_off'
                    service_endpoint = f"{api_url.rstrip('/')}/services/{service_domain}/{service}"
                    payload = {"entity_id": eid}
                    try:
                        resp = requests.post(service_endpoint, headers=headers, data=json.dumps(payload), timeout=10)
                        resp.raise_for_status()
                        st.session_state['ha_dashboard_toggle_pending'][pending_key] = True
                        st.success(f"Sent '{service}' command to {name}.")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Failed to send command: {ex}")
                elif toggled == is_on and st.session_state['ha_dashboard_toggle_pending'].get(pending_key, False):
                    st.session_state['ha_dashboard_toggle_pending'][pending_key] = False
            with st.expander(f"{section} Table ({len(devs)})", expanded=False):
                table = []
                for e in devs:
                    attrs = e.get('attributes', {})
                    state = e.get('state', 'off')
                    available = attrs.get('available', None)
                    assumed_state = attrs.get('assumed_state', None)
                    if state == 'unavailable':
                        online_status = '❌'
                    elif state == 'unknown':
                        online_status = '❓'
                    elif available is True:
                        online_status = '✅'
                    elif available is False:
                        online_status = '❌'
                    elif assumed_state is not None:
                        online_status = '✅' if not assumed_state else '❓'
                    else:
                        online_status = '✅'
                    table.append({
                        'Available': online_status,
                        'Friendly Name': attrs.get('friendly_name', ''),
                        'Entity ID': e.get('entity_id', ''),
                        'State': state,
                        'Device Class': attrs.get('device_class', ''),
                    })
                df = pd.DataFrame(table)
                if not df.empty:
                    columns = ['Available', 'Friendly Name', 'Entity ID', 'State', 'Device Class']
                    df = df[[col for col in columns if col in df.columns]]
                    st.dataframe(df, use_container_width=True, hide_index=True)
        elif section == 'Motion Sensors':
            table = []
            now = datetime.now(timezone.utc).timestamp()
            for e in devs:
                attrs = e.get('attributes', {})
                state = e.get('state', '')
                # Icon for motion state
                icon = '🚶‍♂️' if state == 'on' else '💤' if state == 'off' else '❓'
                last_changed = e.get('last_changed', '')
                motion_ts_epoch = 0
                motion_ago = ''
                motion_ts_est = ''
                if last_changed:
                    try:
                        dt = datetime.fromisoformat(last_changed.replace('Z', '+00:00'))
                        motion_ts_epoch = dt.timestamp()
                        ago = now - motion_ts_epoch
                        if ago < 60:
                            motion_ago = f"{int(ago)}s ago"
                        elif ago < 3600:
                            motion_ago = f"{int(ago//60)}m ago"
                        elif ago < 86400:
                            motion_ago = f"{int(ago//3600)}h ago"
                        else:
                            motion_ago = f"{int(ago//86400)}d ago"
                        est = dt.astimezone(pytz.timezone('US/Eastern'))
                        motion_ts_est = est.strftime('%Y-%m-%d %I:%M:%S %p %Z')
                    except Exception:
                        motion_ago = ''
                        motion_ts_est = ''
                table.append({
                    '': icon,
                    'Friendly Name': attrs.get('friendly_name', ''),
                    'Entity ID': e.get('entity_id', ''),
                    'State': state,
                    'Last Motion (EST)': motion_ts_est,
                    'Motion Time Ago': motion_ago,
                    'Battery': attrs.get('battery_level', ''),
                    'Temperature': attrs.get('temperature', ''),
                    '_motion_ts_epoch': motion_ts_epoch
                })
            df = pd.DataFrame(table)
            if not df.empty:
                df = df.sort_values(by='_motion_ts_epoch', ascending=False).drop(columns=['_motion_ts_epoch'])
                columns = ['', 'Friendly Name', 'Entity ID', 'State', 'Last Motion (EST)', 'Motion Time Ago', 'Battery', 'Temperature']
                df = df[[col for col in columns if col in df.columns]]
                st.dataframe(df, use_container_width=True, hide_index=True)
        elif section == 'Other':
            with st.expander(f"{section} ({len(devs)})", expanded=False):
                table = []
                for e in devs:
                    attrs = e.get('attributes', {})
                    table.append({
                        'Entity ID': e.get('entity_id', ''),
                        'Friendly Name': attrs.get('friendly_name', ''),
                        'State': e.get('state', ''),
                        'Domain': e.get('entity_id', '').split('.')[0],
                        'Device Class': attrs.get('device_class', ''),
                    })
                df = pd.DataFrame(table)
                if not df.empty:
                    st.dataframe(df, use_container_width=True, hide_index=True)
    # Show raw data
    with st.expander("Show raw API data", expanded=False):
        st.code(json.dumps(entities, indent=2), language="json")