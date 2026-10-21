"""Pico RP2040, MicroPython. Copy this file to Pico, run scan() from USB REPL.
20 passive RC ports. EXPLICITLY a 3.3 V diagnostic, not an ohmmeter.
Do not connect powered or charged DUTs. Read DESIGN.md before enabling.
"""
from machine import Pin
import rp2
import time

GPIO = (0,1,2,3,4,5,6,7,8,9,28,27,26,22,21,20,19,18,17,16)
PIO_HZ = 2_000_000
# Two cycles per count, 1 us. INIT and sampling add a fixed ~1us calibrated offset.
@rp2.asm_pio(set_init=rp2.PIO.IN_LOW)
def falling():
    pull(block)
    mov(x, osr)
    set(pins, 0)
    set(pindirs, 1)
    label("sample")
    jmp(pin, "high")
    jmp("done")
    label("high")
    jmp(x_dec, "sample")
    label("done")
    mov(isr, x)
    push(block)
    set(pindirs, 0)
    label("park")
    jmp("park")

def release():
    for gpio in GPIO:
        Pin(gpio, Pin.IN, pull=None)

def measure(sense, sink, timeout_us=5_000_000):
    """Test numbers 1..20. Return threshold time/status, not resistance."""
    if sense == sink or not (1 <= sense <= 20 and 1 <= sink <= 20):
        raise ValueError("distinct test ports 1..20 required")
    if not 100 <= timeout_us <= 60_000_000:
        raise ValueError("timeout outside 100us..60s")
    sm = rp2.StateMachine(0)
    sm.active(0)
    release()  # restores SIO mux after preceding PIO operation
    try:
        for gpio in GPIO:
            Pin(gpio, Pin.OUT, value=1)
        time.sleep_ms(50)
        initial_ok = all(Pin(gpio).value() for gpio in GPIO)
        release()
        sm.init(falling, freq=PIO_HZ, jmp_pin=Pin(GPIO[sense-1]),
                set_base=Pin(GPIO[sink-1]))
        sm.put(timeout_us)
        sm.active(1)
        start = time.ticks_ms()
        while sm.rx_fifo() == 0:
            if time.ticks_diff(time.ticks_ms(), start) > timeout_us//1000+1000:
                raise RuntimeError("PIO watchdog")
            time.sleep_ms(1)
        remaining = sm.get()
        # PIO x_dec post-decrements zero even when branch is not taken.
        if remaining == 0xffffffff:
            return None, "timeout" if initial_ok else "precharge_failed"
        return timeout_us-remaining, "ok" if initial_ok else "precharge_failed"
    finally:
        sm.active(0)
        release()

def scan(repeats=3, timeout_us=5_000_000):
    """190 unordered pairs, both sink directions, repeated CSV via USB serial."""
    if repeats < 1:
        raise ValueError("positive repeats required")
    print("pair_a,pair_b,sense,sink,repeat,fall_us,status")
    try:
        for a in range(1,21):
            for b in range(a+1,21):
                for sense,sink in ((a,b),(b,a)):
                    for rep in range(repeats):
                        us,status=measure(sense,sink,timeout_us)
                        print(a,b,sense,sink,rep,"" if us is None else us,status,sep=",")
    finally:
        release()

release()
# No auto-scan at USB power-up. User must explicitly run scan().
