"""Smoke test by default. Full preparation/training requires explicit --train."""
import argparse
import subprocess
import sys
from pathlib import Path
from temporal import ALIGNMENT_LABELS

H=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train",action="store_true",help="explicitly prepare all data and train all eight aligned models")
    args=parser.parse_args()
    def run(script,*rest):
        subprocess.run([sys.executable,str(H/script),*rest],check=True)
    if not args.train:
        run("test_temporal.py")
        run("test_envelopes.py")
        run("smoke_alignment.py")
        return
    # Finish all four-band experiments before beginning eight-band preparation/training.
    for prefix in ["4x16-alt","8x8"]:
        layouts=[name for name in ALIGNMENT_LABELS if name.startswith(prefix+"-")]
        run("prepare.py","--layouts",*layouts)
        run("train.py","--layouts",*layouts)
    run("check_trimmed.py")
    run("check_results.py")

if __name__=="__main__":main()
