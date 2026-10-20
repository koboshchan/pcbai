import gzip
import json
from pathlib import Path
import struct
import tempfile
import unittest
import numpy as np
import evaluate as ev


def reply(delta=0.):
    return dict(adc_volts=[1.+delta]+[1.]*9,scores=[0.]*10,raw=[100]*10,settle_ms=70)


class Pico:
    def __init__(self,replies):
        self.replies=iter(replies)
        self.calls=[]
    def call(self,request):
        self.calls.append(request)
        result=next(self.replies)
        if isinstance(result,Exception):
            raise result
        return result


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out=Path(self.tmp.name)/"result.json"
    def run_eval(self,p):
        return ev.evaluate(p,np.zeros((1,28,28),np.uint8),[0],
                           [dict(index=0,label=0,prediction=1)],self.out)
    def evidence(self):
        return json.loads(self.out.read_text())
    def test_success(self):
        p=Pico([{"addresses":[72,73,74]},reply(),reply(.003),reply(),reply(),reply()])
        r=self.run_eval(p)
        self.assertEqual((r["status"],r["correct"],r["mismatches"],r["simulator_correct"]),
                         ("complete",1,1,0))
        self.assertEqual(r["confusion_matrix"][0][0],1)
        self.assertEqual(r["final_zero"]["max_adc_delta_vs_start"],0)
        self.assertEqual(p.calls[-1]["pixels"],[0]*64)
        self.assertTrue(all(c["settle_ms"]==70 for c in p.calls[1:]))
        self.assertEqual(p.calls[2]["pixels"],[63]+[0]*63)
        self.assertEqual(p.calls[3]["pixels"],[0]*63+[63])
    def test_final_zero_failure(self):
        p=Pico([{"addresses":[72,73,74]},reply(),reply(.003),reply(),reply(),
                RuntimeError("unsafe or railed ADC reading [3.484]")])
        with self.assertRaisesRegex(RuntimeError,"3.484"):
            self.run_eval(p)
        r=self.evidence()
        self.assertEqual(r["status"],"failed")
        self.assertEqual(r["completed"],1)
        self.assertIn("3.484",r["final_zero"]["error"])
        self.assertNotIn("accuracy",r)

    def test_midrun_failure_stops(self):
        p=Pico([{"addresses":[72,73,74]},reply(),reply(.003),reply(),
                RuntimeError("unsafe or railed ADC reading [3.484]")])
        with self.assertRaisesRegex(RuntimeError,"3.484"):
            self.run_eval(p)
        r=self.evidence()
        self.assertIn("3.484",r["samples"][0]["error"])
        self.assertEqual(len(p.calls),5)
        self.assertNotIn("final_zero",r)

    def test_no_response_gate(self):
        p=Pico([{"addresses":[72,73,74]}]+[reply() for _ in range(3)])
        with self.assertRaisesRegex(ValueError,"No single-pixel"):
            self.run_eval(p)
        self.assertEqual(len(p.calls),4)
        self.assertEqual(self.evidence()["samples"],[])
    def test_scan_strict(self):
        for scan in ({"addresses":[72,73]}, {"addresses":[72,73,74,75]},None,
                     {"addresses":[72,73,74],"error":"bad"}):
            p=Pico([scan])
            with self.assertRaises(ValueError):
                self.run_eval(p)
            self.assertEqual(len(p.calls),1)
    def test_unsafe_reply_preserved_and_aborted(self):
        for field,value in (("adc_volts",.69),("adc_volts",2.51),
                            ("adc_volts",float("nan")),("scores",17.01),
                            ("scores",float("inf")),("raw",float("nan"))):
            with self.subTest(field=field,value=value):
                response=reply()
                response[field][0]=value
                p=Pico([{"addresses":[72,73,74]},response])
                with self.assertRaises(ValueError):
                    self.run_eval(p)
                r=self.evidence()
                self.assertEqual(r["status"],"failed")
                self.assertIn("response",r["sanity"][0])
                self.assertEqual(len(p.calls),2)
    def test_boundary_values(self):
        response=reply()
        response["adc_volts"][:2]=[.70,2.50]
        response["scores"][:2]=[-17.,17.]
        ev.validate_measurement(response)
    def test_malformed(self):
        for response in ({},dict(reply(),error="fault"),
                         dict(reply(),adc_volts=[1.]*9),
                         dict(reply(),scores=[False]*10),
                         dict(reply(),raw=["1"]*10)):
            with self.assertRaises(ValueError):
                ev.validate_measurement(response)
    def test_timeout_evidence(self):
        p=Pico([{"addresses":[72,73,74]},reply(),reply(.01),reply(),TimeoutError("timeout")])
        with self.assertRaises(TimeoutError):
            self.run_eval(p)
        r=self.evidence()
        self.assertTrue(r["sanity_passed"])
        self.assertEqual(r["samples"][0]["index"],0)
        self.assertIn("timeout",r["error"])
    def test_blank_full(self):
        np.testing.assert_array_equal(ev.area_downsample(np.zeros((28,28),np.uint8)),np.zeros(64))
        np.testing.assert_array_equal(ev.area_downsample(np.full((28,28),255,np.uint8)),np.full(64,63))
        with self.assertRaises(ValueError):
            ev.area_downsample(np.zeros((8,8)))
    def test_nonbinary_rowmajor(self):
        image=np.zeros((28,28),np.uint8)
        image[:,:14]=20
        pixels=ev.area_downsample(image).reshape(8,8)
        np.testing.assert_array_equal(pixels[:,:4],np.full((8,4),5))
        np.testing.assert_array_equal(pixels[:,4:],np.zeros((8,4)))
    def test_idx(self):
        images=Path(self.tmp.name)/"images.gz"
        labels=Path(self.tmp.name)/"labels.gz"
        images.write_bytes(gzip.compress(struct.pack(">IIII",2051,10000,28,28)+bytes(10000*784)))
        labels.write_bytes(gzip.compress(struct.pack(">II",2049,10000)+bytes(10000)))
        x,y=ev.load_dataset(images,labels)
        self.assertEqual(x.shape,(10000,28,28))
        self.assertEqual(y.shape,(10000,))
        labels.write_bytes(gzip.compress(struct.pack(">II",2049,10000)+bytes(9999)))
        with self.assertRaises(ValueError):
            ev.load_dataset(images,labels)
    def test_simulator(self):
        labels=np.zeros(10000,np.uint8)
        rows=[dict(index=i,label=0,prediction=int(i>=944)) for i in range(1000)]
        path=Path(self.tmp.name)/"sim.json"
        data=dict(correct=944,failures=0,rows=rows)
        path.write_text(json.dumps(data))
        self.assertEqual(len(ev.load_simulator(path,labels,100)),100)
        data["rows"][2]["label"]=1
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            ev.load_simulator(path,labels,100)
    def test_no_overwrite(self):
        self.out.write_text("original")
        with self.assertRaises(FileExistsError):
            ev.main(["--images","absent","--labels","absent","--output",str(self.out)])
        self.assertEqual(self.out.read_text(),"original")


if __name__=="__main__":
    unittest.main()
