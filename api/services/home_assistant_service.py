import os
import json
import requests
from datetime import datetime, timezone

import pytz

HA_URL = os.getenv("HOME_ASSISTANT_API_URL", "")
HA_TOKEN = os.getenv("HOME_ASSISTANT_TOKEN", "")

_EST = pytz.timezone("US/Eastern")


def _headers():
    return {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }


def _check_config():
    if not HA_URL or not HA_TOKEN:
        raise ValueError(
            "HOME_ASSISTANT_API_URL and HOME_ASSISTANT_TOKEN must be set in .env"
        )


def _fetch_all_entities():
    _check_config()
    resp = requests.get(
        f"{HA_URL.rstrip('/')}/states", headers=_headers(), timeout=10
    )
    resp.raise_for_status()
    return resp.json()


def get_sensors(entity_filter: str = "", device_class_filter: str = ""):
    entities = _fetch_all_entities()
    sensors = [e for e in entities if e.get("entity_id", "").startswith("sensor.")]
    if entity_filter:
        sensors = [s for s in sensors if entity_filter.lower() in s["entity_id"].lower()]
    if device_class_filter:
        sensors = [
            s for s in sensors
            if s.get("attributes", {}).get("device_class", "") == device_class_filter
        ]

    result = []
    for s in sensors:
        attrs = s.get("attributes", {})
        result.append({
            "entity_id": s.get("entity_id", ""),
            "friendly_name": attrs.get("friendly_name", ""),
            "state": s.get("state", ""),
            "unit": attrs.get("unit_of_measurement", ""),
            "device_class": attrs.get("device_class", ""),
            "last_changed": s.get("last_changed", ""),
        })
    return {"sensors": result, "total": len(result)}


def _time_ago(last_changed: str, now: float):
    if not last_changed:
        return "", ""
    try:
        dt = datetime.fromisoformat(last_changed.replace("Z", "+00:00"))
        ago = now - dt.timestamp()
        if ago < 60:
            motion_ago = f"{int(ago)}s ago"
        elif ago < 3600:
            motion_ago = f"{int(ago // 60)}m ago"
        elif ago < 86400:
            motion_ago = f"{int(ago // 3600)}h ago"
        else:
            motion_ago = f"{int(ago // 86400)}d ago"
        motion_ts_est = dt.astimezone(_EST).strftime("%Y-%m-%d %I:%M:%S %p %Z")
        return motion_ago, motion_ts_est
    except Exception:
        return "", ""


def get_grouped_entities():
    entities = _fetch_all_entities()
    now = datetime.now(timezone.utc).timestamp()

    motion_sensors = []
    lights = []
    switches = []
    security = []
    other = []

    for e in entities:
        eid = e.get("entity_id", "")
        domain = eid.split(".")[0] if "." in eid else ""
        attrs = e.get("attributes", {})
        device_class = attrs.get("device_class", "")
        state = e.get("state", "")

        base = {
            "entity_id": eid,
            "friendly_name": attrs.get("friendly_name", eid),
            "state": state,
            "domain": domain,
            "device_class": device_class,
        }

        if domain == "binary_sensor" and device_class == "motion":
            last_changed = e.get("last_changed", "")
            motion_ago, motion_ts_est = _time_ago(last_changed, now)
            motion_sensors.append({
                **base,
                "last_changed": last_changed,
                "motion_ago": motion_ago,
                "motion_ts_est": motion_ts_est,
                "battery": attrs.get("battery_level", ""),
                "temperature": attrs.get("temperature", ""),
            })
        elif domain == "light":
            lights.append(base)
        elif domain == "switch":
            switches.append(base)
        elif domain == "lock" or (domain == "cover" and device_class == "garage"):
            security.append(base)
        else:
            other.append({**base, "last_changed": e.get("last_changed", "")})

    motion_sensors.sort(key=lambda x: x.get("last_changed", ""), reverse=True)

    return {
        "motion_sensors": motion_sensors,
        "lights": lights,
        "switches": switches,
        "security": security,
        "other": other,
    }


def call_service(domain: str, service: str, entity_id: str):
    _check_config()
    endpoint = f"{HA_URL.rstrip('/')}/services/{domain}/{service}"
    resp = requests.post(
        endpoint,
        headers=_headers(),
        data=json.dumps({"entity_id": entity_id}),
        timeout=10,
    )
    resp.raise_for_status()
    return {"success": True}
