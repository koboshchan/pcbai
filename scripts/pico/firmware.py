"""RAM-loadable RP2040 USB JSON controller. Outputs disabled until measure."""
from machine import Pin, SPI, I2C
import rp2
import time
import sys
import json
from array import array
from uctypes import addressof
from encoding import words, validate_pixels, score_voltage


@rp2.asm_pio(out_init=rp2.PIO.OUT_LOW,
             sideset_init=(rp2.PIO.OUT_LOW, rp2.PIO.OUT_LOW),
             out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=32)
def pulse_density():
    # side bit0=GP17 latch, bit1=GP18 clock. Each frame is 196 clocks.
    set(x, 31).side(0)
    label("first")
    out(pins, 1).side(0)
    nop().side(2)
    jmp(x_dec, "first").side(0)
    set(x, 31).side(0)
    label("second")
    out(pins, 1).side(0)
    nop().side(2)
    jmp(x_dec, "second").side(0)
    nop().side(1)
    nop().side(0)


class Controller:
    def __init__(self):
        self.oe = Pin(16, Pin.OUT, value=1)
        self.bus = I2C(0, sda=Pin(4), scl=Pin(5), freq=100000, timeout=50000)
        self.sm = self.data = self.reload = None
        self.buffer = self.pointer = None
        self.adc_trace = []

    def off(self):
        self.oe.value(1)
        for d in (self.reload, self.data):
            if d is not None:
                d.ctrl = d.pack_ctrl(enable=False)
                d.active(0)
        if self.sm is not None:
            self.sm.active(0)
        for d in (self.reload, self.data):
            if d is not None:
                d.close()
        self.sm = self.data = self.reload = None
        self.buffer = self.pointer = None

    def scan(self):
        self.off()
        return {"addresses": self.bus.scan()}

    def drive(self, pixels):
        validate_pixels(pixels)
        self.off()
        self.buffer = array("I", words(pixels))
        self.pointer = array("I", [addressof(self.buffer)])
        self.sm = rp2.StateMachine(0, pulse_density, freq=8000000,
                                  out_base=Pin(19), sideset_base=Pin(17))
        self.data = rp2.DMA()
        self.reload = rp2.DMA()
        dc = self.data.pack_ctrl(size=2, inc_read=True, inc_write=False,
                                 bswap=False, treq_sel=0,
                                 chain_to=self.reload.channel)
        rc = self.reload.pack_ctrl(size=2, inc_read=False, inc_write=False,
                                   bswap=False)
        self.data.config(read=self.buffer, write=self.sm,
                         count=len(self.buffer), ctrl=dc)
        # AL3_READ_ADDR_TRIG starts data channel and reloads transfer count.
        self.reload.config(read=self.pointer,
                           write=self.data.registers[15:16], count=1, ctrl=rc)
        self.sm.active(1)
        self.data.active(1)
        time.sleep_ms(2)  # complete one cycle before enabling outputs
        self.oe.value(0)

    def read_adc(self, address, channel):
        cfg = 0x8000 | ((4 + channel) << 12) | 0x0200 | 0x0100 | 0x00e0 | 3
        self.bus.writeto_mem(address, 1, cfg.to_bytes(2, "big"))
        # Allow the 25 us power-up interval before testing OS.
        time.sleep_us(50)
        start = time.ticks_ms()
        while True:
            config = int.from_bytes(self.bus.readfrom_mem(address, 1, 2), "big")
            if (config & 0x7fff) != (cfg & 0x7fff):
                raise RuntimeError("ADC config readback mismatch")
            if config & 0x8000:
                break
            if time.ticks_diff(time.ticks_ms(), start) > 25:
                raise RuntimeError("ADC conversion timeout")
            time.sleep_us(200)
        raw = int.from_bytes(self.bus.readfrom_mem(address, 0, 2), "big")
        raw = raw - 65536 if raw & 32768 else raw
        self.adc_trace.append({"address":address,"channel":channel,
                               "ticks_ms":start,"elapsed_ms":time.ticks_diff(time.ticks_ms(),start),
                               "config":config,"raw":raw,"attempt":1,"retry_count":0})
        return raw

    def measure(self, pixels, settle_ms=70, repeats=3):
        validate_pixels(pixels)
        if type(settle_ms) is not int or not 70 <= settle_ms <= 2000:
            raise ValueError("settle_ms must be 70..2000")
        if type(repeats) is not int or not 1 <= repeats <= 20:
            raise ValueError("repeats must be 1..20")
        if self.bus.scan() != [72, 73, 74]:
            raise RuntimeError("expected ADS1115 addresses 0x48,0x49,0x4a")
        self.adc_trace = []
        started = time.ticks_us()
        self.drive(pixels)
        try:
            time.sleep_ms(settle_ms)
            readings = []
            for _ in range(repeats):
                row = [self.read_adc(72 + i // 4, i % 4) for i in range(10)]
                volts = [r * .000125 for r in row]
                if any(not .70 <= v <= 2.50 or
                       abs(score_voltage(v)) > 17 for v in volts):
                    raise RuntimeError("unsafe or railed ADC reading " + str(volts))
                readings.append(row)
            raw = [sum(r[i] for r in readings) / repeats for i in range(10)]
            adc = [r * .000125 for r in raw]
            return {"raw": raw, "raw_repeats": readings, "adc_volts": adc,
                    "adc_trace": self.adc_trace,
                    "scores": [score_voltage(v) for v in adc],
                    "settle_ms": settle_ms, "repeats": repeats,
                    "elapsed_us": time.ticks_diff(time.ticks_us(), started),
                    "pdm_cycle_us": 1543.5, "pio_hz": 8000000}
        finally:
            self.off()


def main():
    c = Controller()
    print(json.dumps({"ready": True, "protocol": 1}))
    try:
        while True:
            line = sys.stdin.readline(4097)
            if not line:
                break
            try:
                if len(line) > 4096 or not line.endswith("\n"):
                    raise ValueError("request exceeds line limit")
                req = json.loads(line)
                op = req.get("op")
                if op == "scan":
                    reply = c.scan()
                elif op == "measure":
                    reply = c.measure(req["pixels"], req.get("settle_ms", 70),
                                      req.get("repeats", 3))
                elif op == "off":
                    c.off()
                    reply = {"off": True}
                elif op == "quit":
                    c.off()
                    print(json.dumps({"off": True}))
                    break
                else:
                    raise ValueError("unknown operation")
            except Exception as exc:
                c.off()
                reply = {"error": str(exc), "adc_trace": c.adc_trace,
                         "retry_policy":"stop on first fault; no outlier retries"}
            print(json.dumps(reply))
    finally:
        c.off()
