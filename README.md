## Touch Sensor Module – MicroPython on RP2040 using PIO + 2 Resistors

The `TouchSensor` class implements a capacitive touch sensor using a relaxation oscillator principle, driven by a PIO state machine on the RP2040. The touch pad is connected with:

- A **470 kΩ resistor** to ground.
- A **1 kΩ resistor** to a GPIO pin (used for charge/discharge timing).

### Operation

Calling `touch_sensor.trigger()` initiates a single acquisition cycle:

1. The PIO drives the GPIO pin high for **20 µs** to charge the plate.
2. The pin is then set to input mode.
3. The PIO measures the discharge time until the pin reaches logic low.

Typical timing:  When a proper earth is establihed (like USB cable to PC, or DSO attachment,the timings vary.  I found 470k/1k with a 2us threshold works for me
- 100k/10k earthed:   idle 1.2 - 1.2   touched 2.3 - 3.8
- 470k/10k no earth:  idle 1.2 - 1.2   touched 1.6 - 2.4

- 470k/0k  earthed:   idle 1.5 - 1.6   touched 4.5 - 4.9
- 470k/0k no earth:   idle 1.5 - 1.6   touched 2.5 - 4.8

- 470k/1k  earthed:   idle 1.6 - 1.7   touched 3.5 - 2.8
- **470k/1k no earth**:   idle 1.5 - 1.6   touched 2.5 - 2.8

The acquisition frequency is controlled externally (typically 5–10 ms intervals). The ISR executes in under 0.9 µs, ensuring low-latency sampling.

You can access the most recent average discharge time using:

```python
touch_sensor.average
```

### Touch Sequence Decoder

The module includes a built-in decoder that captures tap patterns, similar to Morse code:

- `'S'` for a short tap
- `'L'` for a long tap

For example, a sequence like **short-short-long-long-short** will return:

```python
SSLLS
```

via:

```python
new_symbol = touch_sensor.decoded
```

### Debugging (Optional)

- **GPIO 8** can be used to observe discharge activity directly on a scope or analyser.

---

### Usage

#### Initialisation

```python
touch_sensor = TouchSensor(pin=7)
```

Initialises the PIO state machine and configures the IRQ for processing measurements.

#### Triggering Measurements

```python
touch_sensor.trigger()
```

Sends a trigger to the PIO to begin a new measurement cycle.

#### Periodic Sampling

```python
touch_timer.init(period=10, mode=Timer.PERIODIC, callback=touch_timer_cb)
```

A hardware timer periodically calls `trigger()`. Here, the sample rate is 100 Hz (every 10 ms).

#### Decoding Touch Sequences

In your main loop:

```python
new_symbol = touch_sensor.decoded
if new_symbol:
    print("Decoded:", new_symbol)
```

Decoded symbols are available once the input sequence times out (default 1000 ms with no touch).

---

### Notes

- Sampling is **non-blocking** and managed via hardware timer.
- The average filter smooths discharge time variability.
- Timing bounds (`TOUCH_TIME_MIN`, `TOUCH_TIME_MAX`) ensure robustness against spurious signals.

---
