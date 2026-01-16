# zabbix-openhasp-semaphore

Visual monitoring indicator for Zabbix using openHASP devices.

Проект предназначен для отображения общего состояния Zabbix
на одном или нескольких экранах openHASP в виде цветового индикатора
(«светофора»).
## Links

- **openHASP:** https://www.openhasp.com
- **Zabbix:** https://www.zabbix.com

---
![Zabbix openHASP semaphore](images/OpenHASP.png)

## 🇬🇧 English

### Overview

`zabbix-openhasp-semaphore` is a Python script that:

- Connects to **Zabbix 7.x** via **JSON-RPC API**
- Analyzes current **active problems**
- Determines the **maximum problem severity**
- Sends the resulting status (green / yellow / red)
  to one or multiple **openHASP** devices via **MQTT**

The visual severity level matches what you see in the Zabbix web interface.

---

### Severity to Color Mapping

| Zabbix Severity | Meaning               | Color  |
|-----------------|----------------------|--------|
| 0–1             | OK / Information     | Green  |
| 2–3             | Warning / Average    | Yellow |
| 4–5             | High / Disaster      | Red    |

---

![Zabbix openHASP semaphore Warning](images/screenshot-01.png)  
*Zabbix openHASP semaphore WARNING screen*

![Zabbix openHASP semaphore Critical](images/screenshot-00.png)  
*Zabbix openHASP semaphore Critical screen*

![Zabbix openHASP semaphore NO DATA](images/screenshot-02.png)  
*Zabbix openHASP semaphore NO DATA screen*

---

### What is taken into account

- Only **active problems**
- **Disabled triggers are ignored**
- **Disabled hosts are ignored**
- Host association is resolved via:
  - `event.get`
  - fallback to `trigger.get` if needed
- Host information is logged as:
  - Technical host name
  - Visible name (as in Zabbix UI)

---

### Requirements

- Python 3.8+
- Zabbix **7.x**
- openHASP devices
- MQTT broker

Python dependencies:
```bash
pip install requests paho-mqtt
````

---

### Configuration

All configuration is done inside the script:

```python
ZABBIX_URL = "http://127.0.0.1:8080/api_jsonrpc.php"
ZABBIX_API_TOKEN = "YOUR_ZABBIX_API_TOKEN"

MQTT_BROKER = "mqtt.example.com"
MQTT_USER = "mqtt_user"
MQTT_PASS = "mqtt_pass"

OPENHASP_DEVICES = [
    "semaphore_01",
    "semaphore_02",
    "semaphore_03"
]
```

Each device will receive identical status updates.

---

### How it works

1. Query Zabbix API for current problems
2. Filter out:

   * disabled triggers
   * disabled hosts
3. Find maximum severity
4. Publish color and time to all openHASP devices via MQTT

---

### Running

Manual run:

```bash
./semafor.py
```

Cron example:

```cron
*/1 * * * * root /opt/semafor.py
```

---

### Debug mode

Enable detailed output:

```python
DEBUG = True
```

This will log:

* Full API payloads (optional)
* Detected problems
* Associated hosts
* Final severity decision

---

## 🇷🇺 Русский

### Описание

`zabbix-openhasp-semaphore` — это Python-скрипт, который:

* Подключается к **Zabbix 7.x** через **JSON-RPC API**
* Анализирует текущие **активные проблемы**
* Определяет **максимальный уровень серьёзности**
* Отправляет итоговое состояние (green / yellow / red)
  на один или несколько экранов **openHASP** через **MQTT**

Цвет полностью соответствует тому, что отображается в веб-интерфейсе Zabbix.

---

### Соответствие уровней и цветов

| Уровень Zabbix | Значение          | Цвет    |
| -------------- | ----------------- | ------- |
| 0–1            | OK / Information  | Зелёный |
| 2–3            | Warning / Average | Жёлтый  |
| 4–5            | High / Disaster   | Красный |

---

### Что учитывается

* Только **активные проблемы**
* **Отключённые триггеры игнорируются**
* **Отключённые хосты игнорируются**
* Привязка проблемы к хосту определяется через:

  * `event.get`
  * резервно через `trigger.get`
* В логах выводятся:

  * имя узла (host)
  * видимое имя (Visible name)

---

### Требования

* Python 3.8+
* Zabbix **7.x**
* openHASP
* MQTT брокер

Зависимости Python:

```bash
pip install requests paho-mqtt
```

---

### Настройка

Все параметры задаются в коде:

```python
OPENHASP_DEVICES = [
    "semaphore_01",
    "semaphore_02"
]
```

Один и тот же статус отправляется на все устройства.

---

### Принцип работы

1. Получение проблем из Zabbix
2. Фильтрация отключённых объектов
3. Определение максимального severity
4. Отправка состояния в openHASP через MQTT

---

### Запуск

Вручную:

```bash
./semafor.py
```

Через cron:

```cron
*/1 * * * * root /opt/semafor.py
```

---

### Отладка

```python
DEBUG = True
```

В этом режиме выводится:

* информация по проблемам
* хосты, вызвавшие срабатывание
* итоговое решение по цвету

---

## License

MIT
