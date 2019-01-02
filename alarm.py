#!/usr/bin/python

import logging
import os
import sys
import threading
import time
import timeit

# Needed for running on LibreELEC
sys.path.append("/storage/.kodi/addons/virtual.rpi-tools/lib")
sys.path.append('/storage/.kodi/addons/script.module.requests/lib/')
sys.path.append('/storage/.kodi/addons/script.module.urllib3/lib/')
sys.path.append('/storage/.kodi/addons/script.module.chardet/lib/')
sys.path.append('/storage/.kodi/addons/script.module.certifi/lib/')
sys.path.append('/storage/.kodi/addons/script.module.idna/lib/')

import RPi.GPIO as GPIO
import requests

from config import *

DEBUG = False if len(sys.argv) > 1 and "".join(sys.argv[1:]) == "EXTREME" else True


def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUZZER_CTRL_PIN, GPIO.OUT)
    GPIO.setup(BUTTON_CTRL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def close_gpio():
    GPIO.cleanup(BUTTON_CTRL_PIN)
    GPIO.cleanup(BUZZER_CTRL_PIN)


def beep(duration, pause):
    try:
        logger.debug("Beeeeeep {} senconds".format(duration))
        GPIO.output(BUZZER_CTRL_PIN, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(BUZZER_CTRL_PIN, GPIO.LOW)
        time.sleep(pause)
    except RuntimeError:
        pass


def check_button():
    for check in range(TRY_DURATION * 20):
        if not check % 100 and get_humidity() > SHOWER_TRIGGER * 100:
            logger.info("Stopped beeping after {0:.2f} seconds because humidity is at {0:.2f}%".format((check * 0.05),
                                                                                                       get_humidity() / 100))
            return
        if not GPIO.input(BUTTON_CTRL_PIN):
            logger.info("Stopped beeping because button was pressed after {0:.2f} seconds".format(check * 0.05))
            return
        time.sleep(0.05)
    logger.info("Stopped beeping because no reaction after {0:.2f} seconds ".format(check * 0.05))


def piep_thread(stop, kill):
    while not kill.is_set():
        if not stop.is_set():
            logger.debug("Start playing melody")
        for tone in BEEP_MELODY:
            if not stop.is_set():
                beep(float(tone) / 4, 0.1)
        time.sleep(2)


def get_humidity():
    response = requests.get("http://{}/api/{}/sensors/{}".format(IP, API_KEY, HUMIDITY_SENSOR)).json()
    result = int(response['state']['humidity'])
    logger.debug("Humidity: {}%".format(str(float(result) / 100)))
    return result


def start_stop_alarm(value):
    logger.debug("Set waterboiler " + ("ON" if value else "OFF"))
    data = '{{"on": {}}}'.format('true' if value else 'false')
    requests.put("http://{}/api/{}/lights/{}/state".format(IP, API_KEY, WATER_BOILER_SWITCH), data=data)
    for port in BLOCK_PORTS:
        logger.debug("{} rule for blocking port {}".format("Create" if value else "Delete", port))
        os.system("iptables -{} INPUT -p tcp --dport {} -j REJECT".format('A' if value else 'D', port))


def kelvin(value):
    factor = (KELVIN_MAX - KELVIN_MIN) / (CTMAX - CTMIN)
    if KELVIN_MIN <= value <= KELVIN_MAX:
        return int(CTMIN + (KELVIN_MAX - value) / factor)
    raise ValueError


def lights_on(kill):
    i = 0
    while not kill.is_set() and i < DIMMING_STEPS:
        temp = kelvin(round(KELVIN_MIN + (MAX_LIGHT_TEMP - KELVIN_MIN) / DIMMING_STEPS * i))
        data = "{{\"on\":true, \"ct\": {}, \"bri\":{}}}".format(temp, i)
        for light in LIGHTS_IDS:
            response = requests.put("http://{}/api/{}/lights/{}/state".format(IP, API_KEY, light), data=data)
            logger.debug(response.text)
        time.sleep(DIMM_UP_TIME / DIMMING_STEPS)
        i += 1
    if kill.is_set():
        lights_off()


def lights_off():
    for light in LIGHTS_IDS:
        response = requests.put("http://{}/api/{}/lights/{}/state".format(IP, API_KEY, light), data="{\"on\":false}")
        logger.debug(response.text)


def main():
    logger.info("Start alarm clock in {} mode".format("debug" if DEBUG else "EXTREME"))
    start = timeit.default_timer()
    t_kill = threading.Event()
    try:
        threading.Thread(target=lights_on, args=(t_kill,)).start()
        time.sleep(DIMM_UP_TIME - COFFEE_LEAD_TIME)
        start_stop_alarm(True)
        setup_gpio()
        time.sleep(COFFEE_LEAD_TIME)
        t_stop = threading.Event()
        t = threading.Thread(target=piep_thread, args=(t_stop, t_kill))
        t.start()
        stop_timer = WAKE_UP_TRIES
        while get_humidity() < (SHOWER_TRIGGER * 100) and stop_timer:
            t_stop.clear()
            logger.info("Start beeping")
            logger.debug("Try round " + str(WAKE_UP_TRIES - stop_timer + 1))
            check_button()
            t_stop.set()
            snooze_time = SNOOZE if stop_timer < WAKE_UP_TRIES else SNOOZE + SHIT_PAUSE
            logger.info("Snooze for {} seconds".format(snooze_time))
            time.sleep(snooze_time)
            stop_timer = stop_timer - 1
        if not stop_timer + 1:
            logger.info("Stopped because humidity is at {}%".format(get_humidity()))
        else:
            logger.info("Giving up to wake up after {} snoozes".format(WAKE_UP_TRIES))
    finally:
        lights_off()
        t_kill.set()
        start_stop_alarm(False)
        GPIO.output(BUZZER_CTRL_PIN, GPIO.LOW)
        close_gpio()
        logger.info("Exit after {0:.3f} seconds".format(timeit.default_timer() - start))


if __name__ == "__main__":
    if DEBUG:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, format='%(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                            filename="{}/{}".format(os.path.dirname(os.path.realpath(__file__)), 'alarm.log'))
    logger = logging.getLogger(__name__)

    main()
