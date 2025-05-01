# touch_sensor.py
# 
from machine import Pin
from rp2 import PIO, StateMachine, asm_pio
from time import ticks_diff, ticks_ms

# Constants
TOUCH_THRESHOLD = 2.0
TOUCH_TIME_MIN = 0.5
TOUCH_TIME_MAX = 30.0

@asm_pio(set_init=(PIO.OUT_LOW, PIO.OUT_LOW))
def cap_touch():
    # pin 7 for touch, pin 8 for debugging
    wrap_target()
    pull(block) # load counter - effectivelly waits for trigger from python

    # charge plate for 20 µs (400 cycles) 21 cycles/iter × 19 iters = 399 cycles
    set(pindirs, 0b11)
    set(pins,   0b01)
    set(x, 18)
    label("charge_delay")
    nop()[19]
    jmp(x_dec, "charge_delay")
    
    # discharge-time measurement 
    set(pindirs, 0b10)
    set(pins,   0b10)
    mov(x, osr)
    label("measure_loop")
    jmp(pin, "count_down")
    jmp("touched")
    label("count_down")
    jmp(x_dec, "measure_loop")

    # push count and generate interrupt
    label("touched")
    set(pins, 0b00)
    mov(isr, x)
    push(block)
    irq(0)

    wrap()

class TouchSensor:
    AVERAGE_WINDOW = 4  # Number of samples in moving average

    def __init__(self, pin, max_loops=100, sm_freq=20_000_000):
        self.touch_pin = pin
        self.max_loops = max_loops

        self.values = []
        self.last_value = None
        self.stopped = False
        self._decoded_symbol = None

        self.sm = StateMachine(0, cap_touch, freq=sm_freq, set_base=Pin(pin), jmp_pin=Pin(pin))
        self.sm.irq(handler=self._irq_handler)
        self.sm.active(1)

    #@timed_function
    def _irq_handler(self, sm):  #  0.9
        if self.stopped:
            return
        raw = sm.get()
        elapsed_us = (self.max_loops - raw) * 0.1

        if elapsed_us < TOUCH_TIME_MIN or elapsed_us > TOUCH_TIME_MAX:
            return  # discard out-of-range sample

        self.values.append(elapsed_us)
        if len(self.values) > self.AVERAGE_WINDOW:
            self.values.pop(0)

        average = sum(self.values) / len(self.values)
        self._decode_touch(average)

    def _decode_touch(self, value):
        now = ticks_ms()
        if not hasattr(self, '_decoder_state'):
            self._decoder_state = {
                'last_state': False,
                'last_change': now,
                'sequence': '',
                'result_timeout': 1000,
                'short_thresh': 250,
                'long_thresh': 1000
            }

        state = value > TOUCH_THRESHOLD
        if state != self._decoder_state['last_state']:
            duration = ticks_diff(now, self._decoder_state['last_change'])
            if self._decoder_state['last_state']:
                if duration < self._decoder_state['short_thresh']:
                    self._decoder_state['sequence'] += 'S'
                elif duration < self._decoder_state['long_thresh']:
                    self._decoder_state['sequence'] += 'L'
            self._decoder_state['last_change'] = now
            self._decoder_state['last_state'] = state

        elif len(self._decoder_state['sequence']) > 0 and ticks_diff(now, self._decoder_state['last_change']) > self._decoder_state['result_timeout']:
            self._decoded_symbol = self._decoder_state['sequence']
            self._decoder_state['sequence'] = ''

    def trigger(self):
        if not self.stopped:
            self.sm.put(self.max_loops)

    def stop(self):
        self.stopped = True
        self.sm.active(0)

    @property
    def average(self):
        if not self.values:
            return 0.0
        return sum(self.values) / len(self.values)

    @property
    def decoded(self):
        result = self._decoded_symbol
        self._decoded_symbol = None
        return result
