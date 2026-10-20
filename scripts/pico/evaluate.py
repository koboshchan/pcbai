"""Safe, sequential physical MNIST evaluation. No simulator or training runs.

Preprocessing copied verbatim from /work/pcbemu-investigate/examples/mnist_stack.py
area_downsample, as used by /work/v2_emu_run.py (retrieved 2026-10-19).
Predictions use ADC argmax, matching that simulator. No polarity inference.
"""
import argparse
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import time

import numpy as np


def area_downsample(image):
    """Match fixed_model train.py crop, PIL BOX and float32 quantization exactly."""
    from PIL import Image
    a=np.asarray(image,dtype=np.uint8)
    if a.shape!=(28,28):raise ValueError('Expected 28x28 MNIST image')
    im=Image.fromarray(a)
    r=np.where(a.max(axis=1)>20)[0];c=np.where(a.max(axis=0)>20)[0]
    if len(r) and len(c):
        r0,r1=max(0,r[0]-2),min(a.shape[0],r[-1]+3)
        c0,c1=max(0,c[0]-2),min(a.shape[1],c[-1]+3)
        h,w=r1-r0,c1-c0;diff=abs(h-w)
        if h>w:c0=max(0,c0-diff//2);c1=min(a.shape[1],c1+diff-diff//2)
        elif w>h:r0=max(0,r0-diff//2);r1=min(a.shape[0],r1+diff-diff//2)
        im=im.crop((c0,r0,c1,r1))
    volts=np.array(im.resize((8,8),Image.Resampling.BOX),dtype=np.float32).flatten()/255*5
    return np.round(volts/5*63).astype(int)


def load_dataset(images_path, labels_path):
    images=gzip.decompress(Path(images_path).read_bytes())
    labels=gzip.decompress(Path(labels_path).read_bytes())
    if len(images)<16 or struct.unpack(">IIII", images[:16])!=(2051,10000,28,28):
        raise ValueError("Expected official test IDX images header (10000 x 28 x 28)")
    if len(labels)<8 or struct.unpack(">II", labels[:8])!=(2049,10000):
        raise ValueError("Expected official test IDX labels header (10000)")
    if len(images)!=16+10000*784 or len(labels)!=8+10000:
        raise ValueError("Truncated or trailing IDX data")
    x=np.frombuffer(images[16:],dtype=np.uint8).reshape(10000,28,28)
    y=np.frombuffer(labels[8:],dtype=np.uint8)
    if np.any(y>9):
        raise ValueError("Invalid digit label")
    return x,y


def load_simulator(path, labels, count):
    data=json.loads(Path(path).read_text())
    rows=data["rows"]
    if len(rows)!=1000 or data.get("correct")!=944 or data.get("failures")!=0:
        raise ValueError("Expected requested_1000 simulator baseline 944/1000, no failures")
    ordered=sorted(rows,key=lambda row:row["index"])
    for index,row in enumerate(ordered):
        if (row["index"]!=index or row["label"]!=int(labels[index])
                or type(row["prediction"]) is not int or not 0<=row["prediction"]<=9):
            raise ValueError("Simulator indices, labels or predictions do not match test data")
    if sum(row["prediction"]==row["label"] for row in ordered)!=944:
        raise ValueError("Simulator baseline correctness inconsistent")
    return ordered[:count]


def validate_measurement(response):
    if not isinstance(response,dict) or response.get("error"):
        raise ValueError("Pico measurement error: "+repr(response))
    for field, low, high in (("adc_volts",.70,2.50),("scores",-17.,17.)):
        values=response.get(field)
        if not isinstance(values,list) or len(values)!=10:
            raise ValueError(field+" must contain 10 values")
        for value in values:
            if (isinstance(value,bool) or not isinstance(value,(int,float))
                    or not math.isfinite(value) or not low<=value<=high):
                raise ValueError(field+" outside safe range or nonfinite: "+repr(values))
    raw=response.get("raw")
    if not isinstance(raw,list) or len(raw)!=10 or any(
        isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v)
        for v in raw
    ):
        raise ValueError("raw must contain 10 finite values")
    return response


def json_safe(value):
    """Keep invalid hardware evidence valid JSON, including NaN/Inf replies."""
    if isinstance(value,float) and not math.isfinite(value):
        return repr(value)
    if isinstance(value,dict):
        return {str(k):json_safe(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):
        return [json_safe(v) for v in value]
    return value


def save_report(path, report):
    path=Path(path)
    temporary=path.with_name(path.name+".tmp")
    with temporary.open("w") as stream:
        json.dump(json_safe(report),stream,indent=2,allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary,path)


def evaluate(pico, images, labels, simulator, output, *, settle_ms=70, repeats=3,
             report=None):
    """Stop on the first failed gate; persist every reply before validating it."""
    report=report if report is not None else {}
    report.update(status="running",sanity=[],samples=[],correct=0,
                  simulator_correct=0,mismatches=0,confusion_matrix=[[0]*10 for _ in range(10)])
    started=time.perf_counter()
    def save():
        report["elapsed_seconds"]=time.perf_counter()-started
        save_report(output,report)
    def measure(pixels, destination):
        before=time.perf_counter()
        try:
            response=pico.call(dict(op="measure",pixels=pixels,
                                    settle_ms=settle_ms,repeats=repeats))
        except BaseException as exc:
            destination.update(error=type(exc).__name__+": "+str(exc),
                               seconds=time.perf_counter()-before)
            save()
            raise
        destination.update(response=response,seconds=time.perf_counter()-before)
        save()
        return validate_measurement(response)
    try:
        save()
        scan=pico.call(dict(op="scan"))
        report["scan"]=scan
        save()
        if not isinstance(scan,dict) or scan.get("error") or scan.get("addresses")!=[72,73,74]:
            raise ValueError("Expected scan addresses [72,73,74]")
        zero=None
        changed=False
        for pixel in (None,0,63):
            pixels=[0]*64
            if pixel is not None:
                pixels[pixel]=63
            row={"name":"all_zero" if pixel is None else "pixel_"+str(pixel),"pixels":pixels}
            report["sanity"].append(row)
            response=measure(pixels,row)
            if zero is None:
                zero=response["adc_volts"]
            else:
                delta=max(abs(a-b) for a,b in zip(zero,response["adc_volts"]))
                row["max_adc_delta_vs_zero"]=delta
                changed=changed or delta>.002
                save()
        if not changed:
            raise ValueError("No single-pixel response differs from zero by more than 0.002 V")
        report["sanity_passed"]=True
        save()
        for index,reference in enumerate(simulator):
            row={"index":index,"label":int(labels[index]),
                 "simulator_prediction":reference["prediction"],
                 "pixels":area_downsample(images[index]).tolist()}
            report["samples"].append(row)
            response=measure(row["pixels"],row)
            prediction=int(np.argmax(response["adc_volts"]))
            row.update(prediction=prediction,correct=prediction==row["label"],
                       simulator_correct=reference["prediction"]==row["label"],
                       mismatch=prediction!=reference["prediction"])
            report["correct"]+=int(row["correct"])
            report["simulator_correct"]+=int(row["simulator_correct"])
            report["mismatches"]+=int(row["mismatch"])
            report["confusion_matrix"][row["label"]][prediction]+=1
            report["completed"]=index+1
            save()
        report["final_zero"]={"name":"all_zero_end","pixels":[0]*64}
        final=measure([0]*64,report["final_zero"])
        report["final_zero"]["max_adc_delta_vs_start"]=max(
            abs(a-b) for a,b in zip(zero,final["adc_volts"]))
        report["status"]="complete"
        report["accuracy"]=report["correct"]/len(simulator)
        save()
        return report
    except BaseException as exc:
        report.update(status="failed",error=type(exc).__name__+": "+str(exc))
        save()
        raise


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images",required=True)
    parser.add_argument("--labels",required=True)
    parser.add_argument("--simulator",default="/home/kit/out/dc1c-substitution-oct19/requested_1000.json")
    parser.add_argument("--output",required=True)
    parser.add_argument("--port")
    parser.add_argument("--count",type=int,default=1000)
    parser.add_argument("--settle-ms",type=int,default=70)
    parser.add_argument("--repeats",type=int,default=3)
    args=parser.parse_args(argv)
    if not 1<=args.count<=1000 or args.settle_ms<70 or args.repeats<1:
        parser.error("count must be 1..1000, settle-ms >=70, repeats >=1")
    output=Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    # Exclusive create prevents accidentally destroying prior hardware evidence.
    with output.open("x") as stream:
        stream.write('{"status":"preparing"}\n')
    report={"status":"preparing","count":args.count,"settle_ms":args.settle_ms,
            "repeats":args.repeats,"selection":"First N official MNIST test images, in IDX order",
            "preprocessing":"mnist_stack.area_downsample, intensity>20/pad2/square-expand/BOX8/float32 6-bit",
            "files":{}}
    try:
        for name in ("images","labels","simulator"):
            path=Path(getattr(args,name))
            report["files"][name]={"path":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
        images,labels=load_dataset(args.images,args.labels)
        simulator=load_simulator(args.simulator,labels,args.count)
        save_report(output,report)
        from host import Pico
        with Pico(port=args.port) as pico:
            evaluate(pico,images,labels,simulator,output,settle_ms=args.settle_ms,
                     repeats=args.repeats,report=report)
    except BaseException as exc:
        report.update(status="failed",error=type(exc).__name__+": "+str(exc))
        save_report(output,report)
        raise
    print(json.dumps({k:report[k] for k in ("status","completed","correct","accuracy",
                                           "simulator_correct","mismatches","elapsed_seconds")}))


if __name__=="__main__":
    main()
