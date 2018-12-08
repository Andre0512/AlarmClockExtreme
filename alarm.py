#!/usr/bin/python

import logging
import sys
import threading
import time

# Needed for running on LibreELEC
sys.path.append("/storage/.kodi/addons/virtual.rpi-tools/lib")
sys.path.append('/storage/.kodi/addons/script.module.requests/lib/')
sys.path.append('/storage/.kodi/addons/script.module.urllib3/lib/')
sys.path.append('/storage/.kodi/addons/script.module.chardet/lib/')
sys.path.append('/storage/.kodi/addons/script.module.certifi/lib/')
sys.path.append('/storage/.kodi/addons/script.module.idna/lib/')

import RPi.GPIO as GPIO
import requests

from secrets import IP, API_KEY

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, format='%(levelname)s - %(message)s')

BUZZER_CTRL_PIN = 2
BUTTON_CTRL_PIN = 18
WATER_BOILER_SWITCH = 6
HUMIDITY_SENSOR = 54

SHOWER_TRIGGER = 85  # Humidity in percent
COFFEE_LEAD_TIME = 180
TRY_DURATION = 180
SNOOZE = 180
SHIT_PAUSE = 300
WAKE_UP_TRIES = 30


def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUZZER_CTRL_PIN, GPIO.OUT)
    GPIO.setup(BUTTON_CTRL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def close():
    GPIO.cleanup(BUZZER_CTRL_PIN)


def piep(duration, pause):
    try:
        logging.debug("Beeeeeep {} senconds".format(duration))
        GPIO.output(BUZZER_CTRL_PIN, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(BUZZER_CTRL_PIN, GPIO.LOW)
        time.sleep(pause)
    except RuntimeError:
        pass


def check_button():
    for x in range(TRY_DURATION * 20):
        if not x % 100:
            humidity = int(
                requests.get("http://{}/api/{}/sensors/{}".format(IP, API_KEY, HUMIDITY_SENSOR)).json()['state'][
                    'humidity'])
            logging.debug("Humidity: " + str(float(humidity) / 100) + "%")
            if humidity > SHOWER_TRIGGER * 100:
                return
        if not GPIO.input(BUTTON_CTRL_PIN):
            return
        time.sleep(TRY_DURATION / 20)


def ducks():
    beat = [1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 4, 1, 1, 1, 1, 4, 1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 4]
    for x in beat:
        piep(float(x) / 4, 0.1)


def piep_thread(stop):
    while True:
        if not stop.is_set():
            ducks()
            logging.debug("beep")
        time.sleep(2)


def main():
    try:
        requests.put("http://{}/api/{}/lights/{}/state".format(IP, API_KEY, WATER_BOILER_SWITCH), data='{"on": true}')
        time.sleep(COFFEE_LEAD_TIME)
        setup()
        t_stop = threading.Event()
        t = threading.Thread(target=piep_thread, args=(t_stop,))
        t.start()
        stop_timer = WAKE_UP_TRIES
        while int(requests.get("http://{}/api/{}/sensors/{}".format(IP, API_KEY, HUMIDITY_SENSOR)).json()['state'][
                      'humidity']) < SHOWER_TRIGGER * 100 and stop_timer:
            setup()
            t_stop.clear()
            check_button()
            close()
            t_stop.set()
            time.sleep(SNOOZE if stop_timer < WAKE_UP_TRIES else SNOOZE + SHIT_PAUSE)
            logging.debug("Round: " + str(WAKE_UP_TRIES - stop_timer))
            stop_timer = stop_timer - 1
    finally:
        close()
        requests.put("http://{}/api/{}/lights/{}/state".format(IP, API_KEY, WATER_BOILER_SWITCH), data='{"on": false}')


if __name__ == "__main__":
    main()
