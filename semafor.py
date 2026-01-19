#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
semafor.py

Скрипт:
- Получает текущие проблемы из Zabbix 7.x по API key
- Определяет максимальный уровень серьёзности (severity)
- Отправляет цветовую индикацию на несколько openHASP экранов через MQTT

Цвета:
- GREEN  : проблем нет или только Information
- YELLOW : Warning / Average
- RED    : High / Disaster
"""

import requests
import sys
import json
from datetime import datetime
import paho.mqtt.publish as publish

# ================== CONFIG ==================

# Zabbix API
ZABBIX_URL = "http://127.0.0.1:8080/api_jsonrpc.php"
ZABBIX_API_TOKEN = "YOUR_ZABBIX_API_TOKEN"

MQTT_BROKER = "mqtt.example.com"
MQTT_USER =   "mqtt_user"
MQTT_PASS =   "mqtt_pass"

# Список openHASP устройств (можно добавлять сколько угодно)
OPENHASP_DEVICES = [
    "semaphore_01",
    "semaphore_02",
    "semaphore_03",
]

DEBUG = True

# ============================================


def log(msg):
    """Отладочный вывод"""
    if DEBUG:
        print(f"[DEBUG] {msg}", file=sys.stderr)


def api_call(method, params=None):
    """
    Универсальный вызов Zabbix API (7.x)
    Авторизация выполняется через API key в HTTP заголовке
    """
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 10
    }

    headers = {
        "Content-Type": "application/json-rpc",
        "Authorization": f"Bearer {ZABBIX_API_TOKEN}"
    }

    r = requests.post(
        ZABBIX_URL,
        json=payload,
        headers=headers,
        timeout=15
    )
    r.raise_for_status()
    data = r.json()

    if "error" in data:
        raise RuntimeError(data["error"])

    return data.get("result", [])


def get_hosts_by_event(eventid):
    """
    Получение хостов, связанных с событием (event)
    Нужно для корректного отображения имени узла
    """
    result = api_call(
        "event.get",
        {
            "eventids": [str(eventid)],
            "selectHosts": ["host", "name", "status"]
        }
    )

    return result[0].get("hosts", []) if result else []


def get_max_problem_severity():
    """
    Основная логика:
    - Берём все активные проблемы
    - Игнорируем disabled триггеры
    - Игнорируем disabled хосты
    - Определяем максимальный severity
    """

    problems = api_call(
        "problem.get",
        {
            "output": ["eventid", "severity", "name", "objectid"],
            "source": 0,        # только триггеры
            "object": 0,
            "suppressed": False,
            "acknowledged": False
        }
    )

    max_sev = 0
    max_items = []

    for p in problems:
        sev = int(p["severity"])

        # Проверяем, что триггер включён
        triggers = api_call(
            "trigger.get",
            {
                "triggerids": [p["objectid"]],
                "output": ["triggerid", "status"]
            }
        )

        # Если все триггеры выключены — пропускаем
        if triggers and not any(int(t["status"]) == 0 for t in triggers):
            continue

        # Получаем хосты через событие
        hosts = get_hosts_by_event(p["eventid"])

        # Fallback: получаем хосты через триггер
        if not hosts and triggers:
            trig_hosts = api_call(
                "trigger.get",
                {
                    "triggerids": [p["objectid"]],
                    "selectHosts": ["host", "name", "status"],
                    "output": "extend"
                }
            )
            if trig_hosts:
                hosts = trig_hosts[0].get("hosts", [])

        # Если все хосты выключены — пропускаем
        if hosts and not any(int(h["status"]) == 0 for h in hosts):
            continue

        # Обновляем максимум
        if sev > max_sev:
            max_sev = sev
            max_items = [(p, hosts)]
        elif sev == max_sev:
            max_items.append((p, hosts))

    # Подробный вывод в отладке
    if max_items:
        log("Problems with MAX severity:")
        for p, hosts in max_items:
            log(f"Severity: {p['severity']}")
            log(f"Problem : {p['name']}")

            if not hosts:
                log(" Host : <NOT RESOLVED>")
            else:
                for h in hosts:
                    log(f" Host node : {h['host']} | Visible : {h['name']}")

            log("-" * 60)

    return max_sev


def publish_openhasp(color):
    """
    Отправка цвета и времени на ВСЕ openHASP устройства
    """
    auth = {"username": MQTT_USER, "password": MQTT_PASS}
    now = datetime.now().strftime("%H:%M")
    text_color = "white" if color == "red" else "black"

    for device in OPENHASP_DEVICES:
        base = f"hasp/{device}/command"

        # Фон страницы
        publish.single(
            f"{base}/jsonl",
            json.dumps({"page": 1, "id": 0, "bg_color": color}),
            hostname=MQTT_BROKER,
            auth=auth,
            retain=True
        )

        # Отключаем idle
        publish.single(
            base,
            "idle off",
            hostname=MQTT_BROKER,
            auth=auth,
            retain=True
        )

        # Время
        publish.single(
            f"{base}/jsonl",
            json.dumps({
                "page": 1,
                "id": 2,
                "text_color": text_color,
                "text": now
            }),
            hostname=MQTT_BROKER,
            auth=auth,
            retain=True
        )

        log(f"openHASP [{device}] updated: {color}")


# ================== MAIN ==================

if __name__ == "__main__":
    log("Start semafor.py")

    try:
        max_sev = get_max_problem_severity()
        log(f"Max severity: {max_sev}")

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
