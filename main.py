from machine import Pin, I2C, WDT, ADC
import machine
import network
import time
import ntptime

from sht41 import SHT41
from lps22hh import LPS22HH
from webserver import start_server

SSID = "PLAY_Swiatlowodowy_B402"
PASSWORD = "9x6gEw#81S95"

RESTART_AFTER = None  # historia 24h jest trzymana w RAM, wiec nie resetujemy co godzine
wdt = WDT(timeout=60000)

PRESSURE_MIN_HPA = 850
PRESSURE_MAX_HPA = 1100
PRESSURE_REDUCTION_HPA = 0
PRESSURE_FALLBACK_HPA = 1013.25
PRESSURE_READ_ATTEMPTS = 3

BATTERY_ADC_PIN = 1
BATTERY_VOLTAGE_DIVIDER = 2.0
BATTERY_EMPTY_VOLTAGE = 3.3
BATTERY_FULL_VOLTAGE = 4.2

NTP_SERVERS = (
    "pool.ntp.org",
    "0.pool.ntp.org",
    "1.pool.ntp.org",
    "time.google.com",
    "time.cloudflare.com",
)

i2c = I2C(
    0,
    sda=Pin(5),
    scl=Pin(6),
    freq=400000
)

sht = SHT41(i2c)
lps = LPS22HH(i2c)
lps.init()
bat_adc = ADC(Pin(BATTERY_ADC_PIN))
bat_adc.atten(ADC.ATTN_11DB)
last_valid_pressure = None


def is_realistic_pressure(pressure):
    return PRESSURE_MIN_HPA <= pressure <= PRESSURE_MAX_HPA


def reduce_pressure(pressure):
    return pressure + PRESSURE_REDUCTION_HPA


def read_battery_percent():
    raw = bat_adc.read_u16()
    voltage = raw * 3.3 / 65535 * BATTERY_VOLTAGE_DIVIDER
    percent = (voltage - BATTERY_EMPTY_VOLTAGE) * 100 / (
        BATTERY_FULL_VOLTAGE - BATTERY_EMPTY_VOLTAGE
    )

    if percent < 0:
        return 0

    if percent > 100:
        return 100

    return round(percent)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)

    wlan.active(False)
    time.sleep(1)

    wlan.active(True)
    time.sleep(1)

    try:
        wlan.config(pm=0xa11140)  # wyłączenie oszczędzania energii WiFi
    except:
        pass

    if wlan.isconnected():
        wlan.disconnect()
        time.sleep(1)

    print("Laczenie z WiFi...")
    wlan.connect(SSID, PASSWORD)

    for _ in range(30):
        wdt.feed()

        if wlan.isconnected():
            print("WiFi OK")
            print("IP:", wlan.ifconfig()[0])
            return wlan

        time.sleep(1)

    print("Nie udalo sie polaczyc z WiFi")
    return wlan


def read_values():
    global last_valid_pressure

    temp_sht, humidity = sht.read()
    temp_lps = temp_sht
    pressure = None

    for attempt in range(PRESSURE_READ_ATTEMPTS):
        read_pressure, read_temp_lps = lps.read()
        temp_lps = read_temp_lps

        if is_realistic_pressure(read_pressure):
            pressure = read_pressure
            last_valid_pressure = read_pressure
            break

        print("Nierealistyczne cisnienie:", read_pressure, "hPa, proba", attempt + 1)
        time.sleep_ms(50)

    if pressure is None:
        if last_valid_pressure is not None:
            pressure = last_valid_pressure
        else:
            pressure = PRESSURE_FALLBACK_HPA

        print("Uzywam zastepczego cisnienia:", pressure, "hPa")

    avg_temp = (temp_sht + temp_lps) / 2

    return avg_temp, humidity, reduce_pressure(pressure), read_battery_percent()


def sync_time(wdt):
    attempt = 1

    while True:
        for server in NTP_SERVERS:
            wdt.feed()

            try:
                ntptime.host = server
                ntptime.settime()
                print("Czas OK:", server)
                return
            except Exception as e:
                print("Nie udalo sie ustawic czasu z", server, "proba", attempt, e)

            attempt += 1
            wdt.feed()
            time.sleep(2)


wlan = connect_wifi()

if wlan.isconnected():
    sync_time(wdt)

    start_server(
        read_values,
        wlan,
        connect_wifi,
        wdt,
        time.time(),
        RESTART_AFTER
    )
else:
    print("Brak WiFi, restart...")
    time.sleep(5)
    machine.reset()
