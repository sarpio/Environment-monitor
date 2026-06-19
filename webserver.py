import socket
import time
import machine

try:
    import ujson as json
except ImportError:
    import json


with open("index.html", "r") as f:
    HTML_TEMPLATE = f.read()

with open("style.css", "r") as f:
    STYLE_CSS = f.read()

with open("script.js", "r") as f:
    SCRIPT_JS_TEMPLATE = f.read()

MAX_HISTORY_RECORDS = 24
HISTORY_INTERVAL = 60 * 60
HISTORY_FILE = "measurements_history.json"
measurements_history = []
last_history_slot = None


def fmt(value):
    return "{:.1f}".format(value).rstrip("0").rstrip(".")


def fmt_js_number(value, decimals=2):
    return ("{:." + str(decimals) + "f}").format(value)


def is_warsaw_dst(utc_time):
    month = utc_time[1]
    day = utc_time[2]
    hour = utc_time[3]
    weekday = utc_time[6]

    if month < 3 or month > 10:
        return False

    if month > 3 and month < 10:
        return True

    days_since_sunday = (weekday + 1) % 7
    last_sunday = day - days_since_sunday

    if month == 3:
        return last_sunday >= 25 and (day != last_sunday or hour >= 1)

    return last_sunday < 25 or (day == last_sunday and hour < 1)


def warsaw_offset(now):
    if is_warsaw_dst(time.localtime(now)):
        return 2 * 60 * 60

    return 60 * 60


def warsaw_timezone_name(now):
    if is_warsaw_dst(time.localtime(now)):
        return "CEST"

    return "CET"


def fmt_measurement_hour(now):
    current_time = time.localtime(now + warsaw_offset(now))
    return "{:02d}:{:02d} {}".format(
        current_time[3],
        current_time[4],
        warsaw_timezone_name(now)
    )


def measurement_slot(now):
    return int(now // HISTORY_INTERVAL)


def is_full_hour(now):
    current_time = time.localtime(now + warsaw_offset(now))
    return current_time[4] == 0


def load_history():
    global measurements_history, last_history_slot

    try:
        with open(HISTORY_FILE, "r") as f:
            loaded_history = json.load(f)
    except:
        loaded_history = []

    if not isinstance(loaded_history, list):
        loaded_history = []

    measurements_history = loaded_history[-MAX_HISTORY_RECORDS:]
    last_history_slot = None

    if measurements_history:
        last_record = measurements_history[-1]
        last_history_slot = last_record.get("slot")


def save_history():
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(measurements_history, f)
    except Exception as e:
        print("Nie udalo sie zapisac historii:", e)


def add_history_record(temperature, humidity, pressure, now):
    measurements_history.append({
        "slot": measurement_slot(now),
        "hour": fmt_measurement_hour(now),
        "temperature": temperature,
        "humidity": humidity,
        "pressure": round(pressure)
    })

    while len(measurements_history) > MAX_HISTORY_RECORDS:
        measurements_history.pop(0)

    save_history()


def update_history(read_values):
    global last_history_slot

    now = time.time()
    current_slot = measurement_slot(now)

    if not is_full_hour(now):
        return

    if last_history_slot == current_slot:
        return

    temperature, humidity, pressure = read_values()
    add_history_record(temperature, humidity, pressure, now)
    last_history_slot = current_slot


def build_measurement_js(record):
    return (
        "{ hour: '" + record["hour"] + "', "
        "temperature: " + fmt_js_number(record["temperature"], 2) + ", "
        "humidity: " + fmt_js_number(record["humidity"], 2) + ", "
        "pressure: " + fmt_js_number(record["pressure"], 0) + " }"
    )


def build_weather_data_js(current_temperature, current_humidity, current_pressure):
    history_js = ",\n        ".join(
        build_measurement_js(record) for record in measurements_history
    )

    return (
        "{\n"
        "    current: {\n"
        "        temperature: " + fmt_js_number(current_temperature, 2) + ",\n"
        "        humidity: " + fmt_js_number(current_humidity, 2) + ",\n"
        "        pressure: " + fmt_js_number(current_pressure, 0) + "\n"
        "    },\n"
        "    measurements: [\n"
        "        " + history_js + "\n"
        "    ]\n"
        "}"
    )


def build_script(current_temperature, current_humidity, current_pressure):
    return SCRIPT_JS_TEMPLATE.replace(
        "{{WEATHER_DATA}}",
        build_weather_data_js(current_temperature, current_humidity, current_pressure)
    )


def create_socket():
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]

    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(2)

    try:
        s.settimeout(2)
    except:
        pass

    return s


def start_server(read_values, wlan, reconnect_wifi, wdt, start_time=None, restart_after=None):
    s = create_socket()

    print("HTTP server started")

    wifi_lost_time = None
    load_history()
    update_history(read_values)

    while True:
        conn = None

        try:
            wdt.feed()
            update_history(read_values)

            if start_time is not None and restart_after is not None:
                if time.time() - start_time > restart_after:
                    print("Planned restart")
                    machine.reset()

            if not wlan.isconnected():
                print("WiFi disconnected")

                if wifi_lost_time is None:
                    wifi_lost_time = time.time()

                wlan = reconnect_wifi()

                if not wlan.isconnected():
                    if time.time() - wifi_lost_time > 120:
                        print("WiFi not recovered, reset")
                        machine.reset()

                    time.sleep(2)
                    continue

                wifi_lost_time = None

                try:
                    s.close()
                except:
                    pass

                s = create_socket()
                print("HTTP socket restarted")

            conn, addr = s.accept()

            try:
                request = conn.recv(1024).decode()
            except:
                request = ""

            if "GET /style.css" in request:
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/css\r\n"
                    "Cache-Control: no-cache\r\n"
                    "Connection: close\r\n"
                    "\r\n"
                    + STYLE_CSS
                )
            elif "GET /script.js" in request:
                temperature, humidity, pressure = read_values()

                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: application/javascript; charset=utf-8\r\n"
                    "Cache-Control: no-cache\r\n"
                    "Connection: close\r\n"
                    "\r\n"
                    + build_script(temperature, humidity, pressure)
                )
            else:
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/html; charset=utf-8\r\n"
                    "Cache-Control: no-cache\r\n"
                    "Connection: close\r\n"
                    "\r\n"
                    + HTML_TEMPLATE
                )

            try:
                conn.sendall(response)
            except:
                conn.send(response)

        except OSError:
            pass

        except Exception as e:
            print("HTTP error:", e)

        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass

        time.sleep_ms(50)
