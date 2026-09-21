#!/usr/bin/env python3
import os
import sys
import json
import subprocess

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
KICAD_PYTHON = "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3"
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

# We will generate daughtercard1a with the clean generator and pure monotonic router
