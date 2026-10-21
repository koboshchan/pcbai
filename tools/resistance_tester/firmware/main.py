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

@rp2.asm_pio()
def self_falling():
    # NO set pins/pindirs instructions: every tested GPIO stays high impedance.
    pull(block)
    mov(x, osr)
    label("sample")
    jmp(pin, "high")
    jmp("done")
    label("high")
    jmp(x_dec, "sample")
    label("done")
    mov(isr, x)
    push(block)
    label("park")
    jmp("park")

def release():
    for gpio in GPIO:
        Pin(gpio, Pin.IN, pull=None)

def discharge(milliseconds=100):
    """Reset fixture history through all twenty finite series resistors.
    100ms is a starting hold, not proof that hidden DUT rail caps are empty.
    """
    for gpio in GPIO:
        Pin(gpio, Pin.OUT, pull=None, value=0)
    time.sleep_ms(milliseconds)

def measure(sense, sink, timeout_us=5_000_000, discharge_ms=100):
    """Ports 1..20; sink=0 selects all-input leakage reference, not a sink."""
    if sense == sink or not (1 <= sense <= 20 and 0 <= sink <= 20):
        raise ValueError("sense 1..20; sink 0 (reference) or distinct port 1..20 required")
    if not 100 <= timeout_us <= 60_000_000:
        raise ValueError("timeout outside 100us..60s")
    if not isinstance(discharge_ms, int) or discharge_ms < 100:
        raise ValueError("discharge_ms must be an integer >=100")
    sm = rp2.StateMachine(0)
    sm.active(0)
    release()  # restores SIO mux after preceding PIO operation
    try:
        discharge(discharge_ms)
        for gpio in GPIO:
            Pin(gpio, Pin.OUT, pull=None, value=1)
        time.sleep_ms(50)
        initial_ok = all(Pin(gpio).value() for gpio in GPIO)
        release()
        if sink:
            sm.init(falling, freq=PIO_HZ, jmp_pin=Pin(GPIO[sense-1]),
                    set_base=Pin(GPIO[sink-1]))
        else:
            sm.init(self_falling, freq=PIO_HZ, jmp_pin=Pin(GPIO[sense-1]))
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

def scan(repeats=8, timeout_us=5_000_000, discharge_ms=100, references=True):
    """190 unordered pairs, both sink directions, repeated CSV via USB serial."""
    if repeats < 1:
        raise ValueError("positive repeats required")
    print("pair_a,pair_b,sense,sink,repeat,fall_us,status,window_us")
    # References first, same discharge/precharge/window/repeats as pair captures.
    # sink=0 is a CSV sentinel, never GPIO0.

    try:
        if references:
            for sense in range(1,21):
                for rep in range(repeats):
                    us,status=measure(sense,0,timeout_us,discharge_ms)
                    print(sense,0,sense,0,rep,"" if us is None else us,status,timeout_us,sep=",")
        for a in range(1,21):
            for b in range(a+1,21):
                for sense,sink in ((a,b),(b,a)):
                    for rep in range(repeats):
                        us,status=measure(sense,sink,timeout_us,discharge_ms)
                        print(a,b,sense,sink,rep,"" if us is None else us,status,timeout_us,sep=",")
    finally:
        release()

release()
# No auto-scan at USB power-up. User must explicitly run scan().
