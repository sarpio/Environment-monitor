from machine import Pin, I2C, WDT
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
    temp_sht, humidity = sht.read()
    pressure, temp_lps = lps.read()

    avg_temp = (temp_sht + temp_lps) / 2

    return avg_temp, humidity, pressure


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
