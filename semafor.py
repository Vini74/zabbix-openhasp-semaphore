#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
semafor.py

- Получает активные проблемы из Zabbix 7.x по API token
- Определяет максимальный severity
- Отправляет индикацию на openHASP экраны через MQTT
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
import paho.mqtt.publish as publish
from typing import Optional, Dict


# ================== ENV ==================

dotenv_loaded = load_dotenv()

# ================== CONFIG ==================

class SemaforConfig:
    def __init__(self):
        # Zabbix
        self.ZABBIX_URL = os.environ.get(
            "ZABBIX_URL",
            "http://127.0.0.1:8080/api_jsonrpc.php"
        )
        self.ZABBIX_API_TOKEN = os.environ.get("ZABBIX_API_TOKEN", "")

        # MQTT
        self.MQTT_BROKER = os.environ.get("MQTT_BROKER", "mqtt.example.com")
        self.MQTT_USER = os.environ.get("MQTT_USER", "")
        self.MQTT_PASS = os.environ.get("MQTT_PASS", "")

        # Behaviour
        self.DEBUG = os.environ.get("DEBUG", "true").lower() == "true"
        self.IGNORE_ACKNOWLEDGED = (
            os.environ.get("IGNORE_ACKNOWLEDGED", "true").lower() == "true"
        )

semafor_config = SemaforConfig()

if semafor_config.DEBUG:
    print(f"[DEBUG] .env loaded: {dotenv_loaded}", file=sys.stderr)

# ================== BACKLIGHT CONFIG ==================

BACKLIGHT_DAY = 100      # Яркость днём (0-255)
BACKLIGHT_NIGHT = 7     # Яркость ночью (0-255)
BACKLIGHT_NIGHT_START = 21  # Начало ночного режима (час)
BACKLIGHT_NIGHT_END = 10     # Конец ночного режима (час)

# ================== LOG ==================

def log(msg: str):
    if semafor_config.DEBUG:
        print(f"[DEBUG] {msg}", file=sys.stderr)


def get_backlight_value() -> int:
    """Определяет яркость подсветки в зависимости от времени суток."""
    current_hour = datetime.now().hour
    is_night = current_hour >= BACKLIGHT_NIGHT_START or current_hour < BACKLIGHT_NIGHT_END
    return BACKLIGHT_NIGHT if is_night else BACKLIGHT_DAY

# ================== openHASP TEMPLATES ==================

OPENHASP_TEMPLATES = {
    "default": [
        lambda base, color, now, text_color: (
            f"{base}/jsonl",
            {"page": 1, "id": 0, "bg_color": color}
        ),
        lambda base, color, now, text_color: (
            base,
            "idle off"
        ),
    ],

    "with_time": [
        lambda base, color, now, text_color: (
            f"{base}/jsonl",
            {"page": 1, "id": 0, "bg_color": color}
        ),
        lambda base, color, now, text_color: (
            base,
            "idle off"
        ),
        lambda base, color, now, text_color: (
            f"{base}/jsonl",
            {
                "page": 1,
                "id": 2,
                "text_color": text_color,
                "text": now
            }
        ),
        lambda base, color, now, text_color: (
            f"{base}/backlight",
            get_backlight_value()
        ),
    ],

    "widgets": [
        lambda base, color, now, text_color: (
            f"{base}/jsonl",
            {"page": 1, "id": 31, "bg_color": color}
        ),
        lambda base, color, now, text_color: (
            base,
            "idle off"
        ),
        lambda base, color, now, text_color: (
            f"{base}/jsonl",
            {
                "page": 1,
                "id": 5,
                "text_color": text_color,
                "text": now
            }
        ),
    ],
}

# ================== openHASP DEVICES ==================

OPENHASP_DEVICES = {
    "semaphore_01": "with_time",
    "semaphore_02": "widgets",
    "semaphore_03": "default",
    "wall_panel":  "default",
}

# Проверка конфигурации на старте
for dev, tpl in OPENHASP_DEVICES.items():
    if tpl not in OPENHASP_TEMPLATES:
        raise RuntimeError(
            f"Device '{dev}' references unknown template '{tpl}'"
        )

# ================== ZABBIX API ==================

def api_call(method: str, params: Optional[Dict] = None):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 1
    }

    headers = {
        "Content-Type": "application/json-rpc",
        "Authorization": f"Bearer {semafor_config.ZABBIX_API_TOKEN}"
    }

    r = requests.post(
        semafor_config.ZABBIX_URL,
        json=payload,
        headers=headers,
        timeout=15
    )
    r.raise_for_status()

    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"])

    return data.get("result", [])

# ================== CORE LOGIC ==================

def get_max_problem_severity() -> int:
    problem_params = {
        "output": ["eventid", "severity", "name", "objectid"],
        "source": 0,
        "object": 0,
        "suppressed": False
    }

    if semafor_config.IGNORE_ACKNOWLEDGED:
        problem_params["acknowledged"] = False

    problems = api_call("problem.get", problem_params)
    if not problems:
        return 0

    trigger_ids = list({p["objectid"] for p in problems})

    triggers = api_call(
        "trigger.get",
        {
            "triggerids": trigger_ids,
            "output": ["triggerid", "status"],
            "selectHosts": ["host", "name", "status"]
        }
    )

    trigger_map = {t["triggerid"]: t for t in triggers}

    max_sev = 0
    max_items = []

    for p in problems:
        sev = int(p["severity"])
        trig = trigger_map.get(p["objectid"])

        if not trig:
            continue

        # trigger disabled
        if int(trig["status"]) != 0:
            continue

        hosts = trig.get("hosts", [])

        # all hosts disabled
        if hosts and not any(int(h["status"]) == 0 for h in hosts):
            continue

        if sev > max_sev:
            max_sev = sev
            max_items = [(p, hosts)]
        elif sev == max_sev:
            max_items.append((p, hosts))

    if max_items:
        log("Problems with MAX severity:")
        for p, hosts in max_items:
            log(f"Severity: {p['severity']}")
            log(f"Problem : {p['name']}")
            for h in hosts:
                log(f" Host : {h['host']} ({h['name']})")
            log("-" * 60)

    return max_sev

# ================== MQTT ==================

def publish_openhasp(color: str):
    auth = {
        "username": semafor_config.MQTT_USER,
        "password": semafor_config.MQTT_PASS
    }

    now = datetime.now().strftime("%H:%M")
    text_color = "white" if color == "red" else "black"

    for device, template_name in OPENHASP_DEVICES.items():
        base = f"hasp/{device}/command"
        template = OPENHASP_TEMPLATES[template_name]

        for command in template:
            topic, payload = command(
                base, color, now, text_color
            )

            publish.single(
                topic,
                payload if isinstance(payload, str) else json.dumps(payload),
                hostname=semafor_config.MQTT_BROKER,
                auth=auth, # type: ignore
                retain=True
            )

        log(f"openHASP [{device}] updated using template '{template_name}'")

# ================== MAIN ==================

if __name__ == "__main__":
    log("Start semafor.py")
    log(f"Ignore acknowledged: {semafor_config.IGNORE_ACKNOWLEDGED}")

    try:
        max_sev = get_max_problem_severity()

        if max_sev >= 4:
            color = "red"
        elif max_sev >= 2:
            color = "yellow"
        else:
            color = "green"

        publish_openhasp(color)

    except Exception as e:
        log(f"FATAL: {e}")
        sys.exit(2)

    log("Finish semafor.py")
