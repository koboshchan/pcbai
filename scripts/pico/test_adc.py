"""Exercise ADC register sequencing without importing RP2040-only modules."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest


class ADCReadTests(unittest.TestCase):
    def controller(self, configs, raw=13472):
        tree = ast.parse(Path(__file__).with_name('firmware.py').read_text())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'read_adc')
        namespace = {'time': SimpleNamespace(sleep_us=lambda _: None, ticks_ms=lambda: 0,
                                             ticks_diff=lambda a,b: a-b)}
        exec(compile(ast.Module(body=[method], type_ignores=[]), '<ADC method>', 'exec'), namespace)
        writes = []
        sequence = iter(configs)
        bus = SimpleNamespace(writeto_mem=lambda *args: writes.append(args),
                              readfrom_mem=lambda a,r,n: (next(sequence) if r == 1 else raw).to_bytes(2,'big'))
        obj = SimpleNamespace(bus=bus, adc_trace=[])
        return obj, writes, namespace['read_adc']

    def test_waits_for_ready_and_records_correct_mux_gain(self):
        obj, writes, read = self.controller([0x63e3,0xe3e3])
        self.assertEqual(read(obj,73,2),13472)
        self.assertEqual(writes,[(73,1,bytes.fromhex('e3e3'))])
        self.assertEqual(obj.adc_trace[0]['retry_count'],0)
        self.assertEqual(obj.adc_trace[0]['channel'],2)

    def test_wrong_mux_readback_fails_closed(self):
        obj, _, read = self.controller([0xd3e3])
        with self.assertRaisesRegex(RuntimeError,'readback mismatch'):
            read(obj,73,2)
        self.assertEqual(obj.adc_trace,[])

    def test_signed_conversion(self):
        obj, _, read = self.controller([0xe3e3],65535)
        self.assertEqual(read(obj,73,2),-1)
