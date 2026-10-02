#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
"""
generate_test_board_70x100.py
-----------------------------
Places all components and configures net connections for the 70x100 mm
analog neural network test PCB in KiCad format.

Circuit Architecture:
  4-Input (X0..X3) -> 2-Hidden Neurons (ReLU) -> 2-Output Summing -> Winner-Take-All (WTA) Comparators

Routing is delegated to the autorouter (Freerouting).
"""

import os
import sys
import pcbnew

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
FOOTPRINT_BASE = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"

FP_PATHS = {
    "R_0805": os.path.join(FOOTPRINT_BASE, "Resistor_SMD.pretty"),
    "C_0805": os.path.join(FOOTPRINT_BASE, "Capacitor_SMD.pretty"),
    "D_SOD123": os.path.join(FOOTPRINT_BASE, "Diode_SMD.pretty"),
    "LED_0805": os.path.join(FOOTPRINT_BASE, "LED_SMD.pretty"),
    "SOIC_14": os.path.join(FOOTPRINT_BASE, "Package_SO.pretty"),
    "SW_DIP": os.path.join(FOOTPRINT_BASE, "Button_Switch_SMD.pretty"),
    "HEADER": os.path.join(FOOTPRINT_BASE, "Connector_PinHeader_2.54mm.pretty"),
    "TESTPOINT": os.path.join(FOOTPRINT_BASE, "TestPoint.pretty"),
    "HOLE": os.path.join(FOOTPRINT_BASE, "MountingHole.pretty"),
}

NET_NAMES = [
    "",
    "GND",
    "+12V",
    "-12V",
    "+5V",
    "X0",
    "X1",
    "X2",
    "X3",
    "SUM_NODE_0",
    "V_SUM0",
    "RECT_NODE_0",
    "RECT_OUT_0",
    "V_ACT0",
    "SUM_NODE_1",
    "V_SUM1",
    "RECT_NODE_1",
    "RECT_OUT_1",
    "V_ACT1",
    "SUM2_NODE_0",
    "V_OUT0",
    "SUM2_NODE_1",
    "V_OUT1",
    "CMP_OUT0",
    "LED1_A",
    "CMP_OUT1",
    "LED0_A",
]

class BoardBuilder:
    def __init__(self):
        self.board = pcbnew.BOARD()
        self.nets = {}
        for name in NET_NAMES:
            if name:
                net_item = pcbnew.NETINFO_ITEM(self.board, name)
                self.board.Add(net_item)
                self.nets[name] = net_item

        self.footprints = {}
        self.init_board_settings()

    def init_board_settings(self):
        settings = self.board.GetDesignSettings()
        settings.m_TrackMinWidth = pcbnew.FromMM(0.25)
        # Outline: 100.0 x 70.0 mm
        corners = [(0.0, 0.0), (100.0, 0.0), (100.0, 70.0), (0.0, 70.0)]
        for i in range(4):
            x1, y1 = corners[i]
            x2, y2 = corners[(i + 1) % 4]
            seg = pcbnew.PCB_SHAPE(self.board)
            seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
            seg.SetLayer(pcbnew.Edge_Cuts)
            seg.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
            seg.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
            seg.SetWidth(pcbnew.FromMM(0.15))
            self.board.Add(seg)

    def add_text(self, text, x, y, size=1.0, layer=pcbnew.F_SilkS):
        txt = pcbnew.PCB_TEXT(self.board)
        txt.SetText(text)
        txt.SetLayer(layer)
        txt.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        txt.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size), pcbnew.FromMM(size)))
        txt.SetTextThickness(pcbnew.FromMM(0.15))
        self.board.Add(txt)

    def add_footprint(self, lib_key, fp_name, ref, val, x, y, rot=0, pin_nets=None):
        lib_path = FP_PATHS[lib_key]
        fp = pcbnew.FootprintLoad(lib_path, fp_name)
        if not fp:
            raise RuntimeError(f"Could not load footprint {fp_name} from {lib_path}")

        fp.SetReference(ref)
        fp.SetValue(val)
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        fp.SetOrientationDegrees(rot)

        ref_prop = fp.Reference()
        ref_prop.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.0), pcbnew.FromMM(1.0)))
        ref_prop.SetTextThickness(pcbnew.FromMM(0.15))

        val_prop = fp.Value()
        val_prop.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.8), pcbnew.FromMM(0.8)))
        val_prop.SetTextThickness(pcbnew.FromMM(0.12))

        self.board.Add(fp)
        self.footprints[ref] = fp

        if pin_nets:
            for pad_num, net_name in pin_nets.items():
                pad = fp.FindPadByNumber(str(pad_num))
                if pad and net_name in self.nets:
                    pad.SetNet(self.nets[net_name])

        return fp

    def get_pad_pos(self, ref, pad_num):
        fp = self.footprints[ref]
        pad = fp.FindPadByNumber(str(pad_num))
        if not pad:
            raise ValueError(f"Pad {pad_num} not found on {ref}")
        pos = pad.GetPosition()
        return (round(pcbnew.ToMM(pos.x), 3), round(pcbnew.ToMM(pos.y), 3))

    def save(self, filepath):
        pcbnew.SaveBoard(filepath, self.board)
        print(f"Board successfully built and saved to {filepath}")

def build_board(output_path):
    bb = BoardBuilder()

    # Silkscreen Metadata & Title
    bb.add_text("ANALOG NEURAL NETWORK TEST BOARD (70x100mm)", 50.0, 3.0, size=1.2)
    bb.add_text("4-IN -> 2-HIDDEN (ReLU) -> 2-OUT (WTA/LEDs)", 50.0, 67.5, size=0.9)
    bb.add_text("PWR", 11.0, 11.5, size=1.0)
    bb.add_text("SW1", 14.0, 27.0, size=0.9)
    bb.add_text("J_IN", 8.0, 52.0, size=0.9)
    bb.add_text("LAYER 1 (SUM+RECT)", 46.0, 11.0, size=1.0)
    bb.add_text("LAYER 2 (SUM+WTA)", 78.0, 11.0, size=1.0)
    bb.add_text("RED: VERT", 86.0, 20.0, size=0.8)
    bb.add_text("GREEN: HORIZ", 86.0, 50.0, size=0.8)

    # 4 Corner Mounting Holes (NPTH 3.2mm M3)
    h1 = bb.add_footprint("HOLE", "MountingHole_3.2mm_M3", "H1", "M3", 4.0, 4.0)
    h2 = bb.add_footprint("HOLE", "MountingHole_3.2mm_M3", "H2", "M3", 96.0, 4.0)
    h3 = bb.add_footprint("HOLE", "MountingHole_3.2mm_M3", "H3", "M3", 4.0, 66.0)
    h4 = bb.add_footprint("HOLE", "MountingHole_3.2mm_M3", "H4", "M3", 96.0, 66.0)
    for h in [h1, h2, h3, h4]:
        h.Reference().SetVisible(False)
        h.Value().SetVisible(False)

    # -------------------------------------------------------------------------
    # Stage 1: Power & Inputs
    # -------------------------------------------------------------------------
    # Power Connector J_PWR (Pin 1=+12V, 2=+5V, 3=GND, 4=-12V) at X=11.0
    bb.add_footprint("HEADER", "PinHeader_1x04_P2.54mm_Vertical", "J_PWR", "PWR", 11.0, 16.0, pin_nets={
        "1": "+12V", "2": "+5V", "3": "GND", "4": "-12V"
    })

    # DIP Switch SW1 (4-DIP SMD) at X=14.0, Y=36.0
    bb.add_footprint("SW_DIP", "SW_DIP_SPSTx04_Slide_6.7x11.72mm_W8.61mm_P2.54mm_LowProfile", "SW1", "4-DIP", 14.0, 36.0, pin_nets={
        "1": "+5V", "2": "+5V", "3": "+5V", "4": "+5V",
        "8": "X0", "7": "X1", "6": "X2", "5": "X3"
    })

    # Input Header J_IN (Vertical 1x5) at X=14.0, Y=52.0
    bb.add_footprint("HEADER", "PinHeader_1x05_P2.54mm_Vertical", "J_IN", "X0..X3/GND", 14.0, 52.0, pin_nets={
        "1": "X0", "2": "X1", "3": "X2", "4": "X3", "5": "GND"
    })

    # Pull-down resistors R_PD0..3 (10k, 0805, rot=0) at X=22.0
    bb.add_footprint("R_0805", "R_0805_2012Metric", "R_PD0", "10k", 22.0, 32.19, rot=0, pin_nets={"1": "X0", "2": "GND"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "R_PD1", "10k", 22.0, 34.73, rot=0, pin_nets={"1": "X1", "2": "GND"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "R_PD2", "10k", 22.0, 37.27, rot=0, pin_nets={"1": "X2", "2": "GND"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "R_PD3", "10k", 22.0, 39.81, rot=0, pin_nets={"1": "X3", "2": "GND"})

    # Test Points for Power
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_+12V", "+12V", 16.0, 5.5, pin_nets={"1": "+12V"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_+5V", "+5V", 6.0, 9.0, pin_nets={"1": "+5V"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_GND", "GND", 18.0, 21.08, pin_nets={"1": "GND"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_-12V", "-12V", 20.0, 64.0, pin_nets={"1": "-12V"})

    # Input Test Points placed along feed corridors to Layer 1
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_X0", "X0", 26.0, 20.0, pin_nets={"1": "X0"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_X1", "X1", 26.0, 24.0, pin_nets={"1": "X1"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_X2", "X2", 26.0, 46.0, pin_nets={"1": "X2"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_X3", "X3", 26.0, 50.0, pin_nets={"1": "X3"})

    # -------------------------------------------------------------------------
    # Stage 2: Layer 1 (U1 TL074 rot=270, Neuron 0 North, Neuron 1 South)
    # -------------------------------------------------------------------------
    u1_nets = {
        "7": "V_SUM0", "6": "SUM_NODE_0", "5": "GND", "4": "+12V", "3": "GND", "2": "RECT_NODE_0", "1": "RECT_OUT_0",
        "8": "V_SUM1", "9": "SUM_NODE_1", "10": "GND", "11": "-12V", "12": "GND", "13": "RECT_NODE_1", "14": "RECT_OUT_1"
    }
    bb.add_footprint("SOIC_14", "SOIC-14_3.9x8.7mm_P1.27mm", "U1", "TL074", 46.0, 35.0, rot=270, pin_nets=u1_nets)

    # Bypass Capacitors for U1
    bb.add_footprint("C_0805", "C_0805_2012Metric", "C1", "0.1uF", 45.365, 28.0, rot=0, pin_nets={"2": "+12V", "1": "GND"})
    bb.add_footprint("C_0805", "C_0805_2012Metric", "C2", "0.1uF", 45.365, 42.0, rot=0, pin_nets={"2": "-12V", "1": "GND"})

    # Neuron 0 Summing Components (North)
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rb1_0", "18k", 30.0, 16.0, rot=0, pin_nets={"1": "-12V", "2": "SUM_NODE_0"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "R1_00", "10k", 30.0, 20.0, rot=0, pin_nets={"1": "X0", "2": "SUM_NODE_0"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "R1_10", "10k", 30.0, 24.0, rot=0, pin_nets={"1": "X1", "2": "SUM_NODE_0"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rf1_0", "10k", 36.0, 16.0, rot=0, pin_nets={"1": "SUM_NODE_0", "2": "V_SUM0"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_SUM0", "V_SUM0", 38.0, 13.0, pin_nets={"1": "V_SUM0"})

    # Neuron 0 Rectifier (ReLU)
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rin_0", "10k", 41.0, 20.0, rot=0, pin_nets={"1": "V_SUM0", "2": "RECT_NODE_0"})
    bb.add_footprint("D_SOD123", "D_SOD-123", "D2_0", "1N4148", 48.54, 26.0, rot=90, pin_nets={"1": "RECT_OUT_0", "2": "RECT_NODE_0"})
    bb.add_footprint("D_SOD123", "D_SOD-123", "D1_0", "1N4148", 52.0, 26.0, rot=270, pin_nets={"1": "V_ACT0", "2": "RECT_OUT_0"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rrelu_0", "10k", 51.0, 16.0, rot=0, pin_nets={"1": "RECT_NODE_0", "2": "V_ACT0"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rpd_act0", "10k", 56.0, 14.0, rot=0, pin_nets={"1": "V_ACT0", "2": "GND"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_ACT0", "V_ACT0", 58.0, 20.0, pin_nets={"1": "V_ACT0"})

    # Neuron 1 Summing Components (South)
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rb1_1", "18k", 30.0, 54.0, rot=0, pin_nets={"1": "-12V", "2": "SUM_NODE_1"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "R1_21", "10k", 30.0, 46.0, rot=0, pin_nets={"1": "X2", "2": "SUM_NODE_1"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "R1_31", "10k", 30.0, 50.0, rot=0, pin_nets={"1": "X3", "2": "SUM_NODE_1"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rf1_1", "10k", 36.0, 54.0, rot=0, pin_nets={"1": "SUM_NODE_1", "2": "V_SUM1"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_SUM1", "V_SUM1", 38.0, 57.0, pin_nets={"1": "V_SUM1"})

    # Neuron 1 Rectifier (ReLU)
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rin_1", "10k", 41.0, 50.0, rot=0, pin_nets={"1": "V_SUM1", "2": "RECT_NODE_1"})
    bb.add_footprint("D_SOD123", "D_SOD-123", "D2_1", "1N4148", 48.54, 44.0, rot=90, pin_nets={"2": "RECT_NODE_1", "1": "RECT_OUT_1"})
    bb.add_footprint("D_SOD123", "D_SOD-123", "D1_1", "1N4148", 52.0, 44.0, rot=90, pin_nets={"1": "V_ACT1", "2": "RECT_OUT_1"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rrelu_1", "10k", 51.0, 54.0, rot=0, pin_nets={"1": "RECT_NODE_1", "2": "V_ACT1"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rpd_act1", "10k", 56.0, 56.0, rot=0, pin_nets={"1": "V_ACT1", "2": "GND"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_ACT1", "V_ACT1", 58.0, 50.0, pin_nets={"1": "V_ACT1"})

    # -------------------------------------------------------------------------
    # Stage 3: Layer 2 & WTA (U2 TL074 rot=270)
    # -------------------------------------------------------------------------
    u2_nets = {
        "7": "V_OUT0", "6": "SUM2_NODE_0", "5": "GND", "4": "+12V", "3": "V_OUT0", "2": "V_OUT1", "1": "CMP_OUT0",
        "8": "V_OUT1", "9": "SUM2_NODE_1", "10": "GND", "11": "-12V", "12": "V_OUT1", "13": "V_OUT0", "14": "CMP_OUT1"
    }
    bb.add_footprint("SOIC_14", "SOIC-14_3.9x8.7mm_P1.27mm", "U2", "TL074", 78.0, 35.0, rot=270, pin_nets=u2_nets)

    # Bypass Capacitors for U2
    bb.add_footprint("C_0805", "C_0805_2012Metric", "C3", "0.1uF", 77.365, 28.0, rot=0, pin_nets={"2": "+12V", "1": "GND"})
    bb.add_footprint("C_0805", "C_0805_2012Metric", "C4", "0.1uF", 77.365, 42.0, rot=0, pin_nets={"2": "-12V", "1": "GND"})

    # Output 0 Summing Components (North)
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rb2_0", "15k", 65.0, 16.0, rot=0, pin_nets={"1": "-12V", "2": "SUM2_NODE_0"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "R2_00", "10k", 65.0, 20.0, rot=0, pin_nets={"1": "V_ACT0", "2": "SUM2_NODE_0"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "R2_10", "10k", 65.0, 24.0, rot=0, pin_nets={"1": "V_ACT1", "2": "SUM2_NODE_0"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rf2_0", "10k", 71.0, 18.0, rot=0, pin_nets={"1": "SUM2_NODE_0", "2": "V_OUT0"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_OUT0", "V_OUT0", 71.0, 14.0, pin_nets={"1": "V_OUT0"})

    # Output 1 Summing Components (South: Reference Threshold)
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rb2_1", "22k", 65.0, 54.0, rot=0, pin_nets={"1": "-12V", "2": "SUM2_NODE_1"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rf2_1", "10k", 71.0, 52.0, rot=0, pin_nets={"1": "SUM2_NODE_1", "2": "V_OUT1"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_OUT1", "V_OUT1", 71.0, 56.0, pin_nets={"1": "V_OUT1"})

    # Output Indicator LEDs & Current-limiting Resistors
    bb.add_footprint("R_0805", "R_0805_2012Metric", "R_LED1", "1k", 86.0, 24.0, rot=0, pin_nets={"1": "CMP_OUT0", "2": "LED1_A"})
    bb.add_footprint("LED_0805", "LED_0805_2012Metric", "LED1", "Red_Vert", 90.5, 24.0, rot=180, pin_nets={"1": "GND", "2": "LED1_A"})

    bb.add_footprint("R_0805", "R_0805_2012Metric", "R_LED0", "1k", 86.0, 46.0, rot=0, pin_nets={"1": "CMP_OUT1", "2": "LED0_A"})
    bb.add_footprint("LED_0805", "LED_0805_2012Metric", "LED0", "Green_Horiz", 90.5, 46.0, rot=180, pin_nets={"1": "GND", "2": "LED0_A"})

    # Output Header J_OUT (Vertical 1x4) at X=96.0, Y=35.0
    bb.add_footprint("HEADER", "PinHeader_1x04_P2.54mm_Vertical", "J_OUT", "OUT", 96.0, 35.0, pin_nets={
        "1": "V_OUT0", "2": "CMP_OUT0", "3": "CMP_OUT1", "4": "V_OUT1"
    })

    # Configure reference visibility and text placement
    for ref, fp in bb.footprints.items():
        if ref.startswith("R") or ref.startswith("C") or ref.startswith("D") or ref.startswith("TP_"):
            fp.Reference().SetVisible(False)
            fp.Value().SetVisible(False)
        elif ref.startswith("U"):
            fp.Value().SetVisible(False)
            fp.Reference().SetPosition(fp.GetPosition())
            fp.Reference().SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.0), pcbnew.FromMM(1.0)))
            fp.Reference().SetTextThickness(pcbnew.FromMM(0.15))

    # All components placed and pads mapped to nets.
    # Routing is delegated to autorouter (Freerouting).
    bb.save(output_path)

if __name__ == "__main__":
    out_pcb = os.path.join(WORKSPACE_DIR, "test_board_70x100.kicad_pcb")
    build_board(out_pcb)
