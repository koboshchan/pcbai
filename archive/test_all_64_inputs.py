import os
import pcbnew

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
def mm(v): return int(v * 1000000)

COL_X = [14.5, 24.5, 34.5, 44.5, 65.5, 75.5, 85.5, 95.5]
NEURON_Y = [18.0, 34.0, 50.0, 66.0]

board_file = os.path.join(WORKSPACE_DIR, "test_inputs_v14.kicad_pcb")
# Load skeleton or generate board
