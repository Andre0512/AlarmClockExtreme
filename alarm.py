#!/usr/bin/python

import sys

# Needed for running on LibreELEC
sys.path.append("/storage/.kodi/addons/virtual.rpi-tools/lib")

import RPi.GPIO as GPIO
import time
import threading
import sys

sys.path.append('/storage/.kodi/addons/script.module.requests/lib/')
sys.path.append('/storage/.kodi/addons/script.module.urllib3/lib/')
sys.path.append('/storage/.kodi/addons/script.module.chardet/lib/')
sys.path.append('/storage/.kodi/addons/script.module.certifi/lib/')
sys.path.append('/storage/.kodi/addons/script.module.idna/lib/')
import requests
import logging

from secrets import IP, API_KEY

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, format='%(levelname)s - %(message)s')

BUZZER_CTRL_PIN = 2
BUTTON_CTRL_PIN = 18


def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUZZER_CTRL_PIN, GPIO.OUT)
    GPIO.setup(BUTTON_CTRL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def close():
    GPIO.cleanup(BUZZER_CTRL_PIN)


def piep(duration, pause):
    try:
        logging.debug("piiiieeeeppp")
        GPIO.output(BUZZER_CTRL_PIN, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(BUZZER_CTRL_PIN, GPIO.LOW)
        time.sleep(pause)
    except RuntimeError:
        pass


def check_button():
    for x in range(3600):
        if not x % 100:
            humidity = int(requests.get("http://{}/api/{}/sensors/54".format(IP, API_KEY)).json()['state']['humidity'])
            logging.debug("Humidity: " + str(float(humidity) / 100) + "%")
            if humidity > 8500:
                return
        if not GPIO.input(BUTTON_CTRL_PIN):
            return
        time.sleep(0.05)


def ducks():
    # Alle meine Entchen
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
        requests.put("http://{}/api/{}/lights/6/state".format(IP, API_KEY), data='{"on": true}')
        time.sleep(180)
        setup()
        t_stop = threading.Event()
        t = threading.Thread(target=piep_thread, args=(t_stop,))
        t.start()
        stop_timer = 30
        while int(requests.get("http://{}/api/{}/sensors/54".format(IP, API_KEY)).json()['state'][
                      'humidity']) < 8500 and stop_timer:
            setup()
            t_stop.clear()
            check_button()
            close()
            t_stop.set()
            time.sleep(180)
            time.sleep(10)
            stop_timer = stop_timer - 1
            logging.debug("Round: " + str(31 - stop_timer))
    finally:
        close()
        requests.put("http://{}/api/{}/lights/6/state".format(IP, API_KEY), data='{"on": false}')


if __name__ == "__main__":
    main()
