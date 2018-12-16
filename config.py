from alarm import DEBUG

IP = ""
API_KEY = ""

# GPIO pins
BUZZER_CTRL_PIN = 2
BUTTON_CTRL_PIN = 18

# Deonz id's
WATER_BOILER_SWITCH = 6
HUMIDITY_SENSOR = 54

# Humidity value to determine shower
SHOWER_TRIGGER = 85

if not DEBUG:
    # Play sequence of beep (1 = 0.25 seconds)
    BEEP_MELODY = [1, 1, 2, 1, 2, 2, 1, 1, 1, 1, 4, 1, 1, 1, 1, 4, 1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 4]
    # Block this ports for not cheating
    BLOCK_PORTS = [22, 8080]
    COFFEE_LEAD_TIME = 180
    TRY_DURATION = 180
    SNOOZE = 180
    SHIT_PAUSE = 300
    WAKE_UP_TRIES = 30
else:
    BEEP_MELODY = [1, 1, 2]
    BLOCK_PORTS = [8080]
    COFFEE_LEAD_TIME = 2
    TRY_DURATION = 3
    SNOOZE = 2
    SHIT_PAUSE = 5
    WAKE_UP_TRIES = 2
