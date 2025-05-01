# main-touch-test.py
from touch_sensor import TouchSensor
from time import sleep_ms
from machine import Timer

TOUCH_THRESHOLD = 2.0  # µs threshold to indicate a touch
STATUS_LED_PIN = 16    # NeoPixel LED pin for touch indication
TOUCH_TIME_MIN = 0.5   # µs minimum valid touch time
TOUCH_TIME_MAX = 30.0  # µs maximum valid touch time

touch_sensor = TouchSensor(pin=7)
# note pin 8 can be used for debugging, it directly indicates discharge time

touch_sensor.trigger()  # get first reading

def touch_timer_cb(touch_timer):
    current_state = touch_sensor.average > TOUCH_THRESHOLD
    #print(current_state)
    touch_sensor.trigger()

touch_timer = Timer()
touch_timer.init(period=10, mode=Timer.PERIODIC, callback=touch_timer_cb)

while True:
    new_symbol = touch_sensor.decoded
    if new_symbol:
        print("Decoded:", new_symbol)
    sleep_ms(50)
