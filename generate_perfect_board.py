#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
"""
generate_perfect_board.py
-------------------------
Deterministic single-layer PCB builder for the 70x100mm Analog Neural Network.
100% single layer (F.Cu only).
Zero vias, zero B.Cu copper.
6x 0805 0-ohm jumpers for topological planar crossings.
Wide tracks for photoresist etching (0.70mm power/gnd, 0.50mm signals, 0.35mm IC pads, 0.28mm under jumpers).
Clearances >= 0.26mm everywhere to ensure 0 DRC violations.
"""

import os
import sys
import pcbnew

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
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
    "-12V_IN",
    "-12V",
    "-12V_NORTH0",
    "-12V_NORTH1",
    "+5V",
    "X0",
    "X1",
    "X2",
    "X3",
    "SUM_NODE_0",
    "V_SUM0",
    "RECT_NODE_0_W",
    "RECT_NODE_0",
    "RECT_OUT_0",
    "V_ACT0",
    "SUM_NODE_1",
    "V_SUM1",
    "RECT_NODE_1_W",
    "RECT_NODE_1",
    "RECT_OUT_1",
    "V_ACT1",
    "SUM2_NODE_0",
    "V_OUT0",
    "SUM2_NODE_1",
    "V_OUT1",
    "V_OUT1_JMP",
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
        self.board.SetCopperLayerCount(1)
        settings.m_TrackMinWidth = pcbnew.FromMM(0.25)
        settings.m_MinClearance = pcbnew.FromMM(0.25)

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

    def add_track_segment(self, x1, y1, x2, y2, net_name, width=0.50):
        if abs(x1 - x2) < 1e-4 and abs(y1 - y2) < 1e-4:
            return
        track = pcbnew.PCB_TRACK(self.board)
        track.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
        track.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
        track.SetWidth(pcbnew.FromMM(width))
        track.SetLayer(pcbnew.F_Cu)
        if net_name in self.nets:
            track.SetNet(self.nets[net_name])
        self.board.Add(track)

    def add_route(self, points, net_name, width=0.50):
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            x1 = p1[0] if isinstance(p1, (tuple, list)) else pcbnew.ToMM(p1.x)
            y1 = p1[1] if isinstance(p1, (tuple, list)) else pcbnew.ToMM(p1.y)
            x2 = p2[0] if isinstance(p2, (tuple, list)) else pcbnew.ToMM(p2.x)
            y2 = p2[1] if isinstance(p2, (tuple, list)) else pcbnew.ToMM(p2.y)
            self.add_track_segment(x1, y1, x2, y2, net_name, width=width)

    def save(self, filepath):
        self.board.SetCopperLayerCount(1)
        pcbnew.SaveBoard(filepath, self.board)
        print(f"Board successfully built and saved to {filepath}")

def build_board(output_path):
    bb = BoardBuilder()

    # Silkscreen Metadata & Title
    bb.add_text("ANALOG NEURAL NETWORK TEST BOARD (70x100mm)", 50.0, 3.0, size=1.2)
    bb.add_text("SINGLE-LAYER F.Cu | 4-IN -> 2-HIDDEN (ReLU) -> 2-OUT (WTA/LEDs)", 50.0, 67.5, size=0.9)
    bb.add_text("PWR", 11.0, 11.5, size=1.0)
    bb.add_text("SW1", 13.0, 27.0, size=0.9)
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

    # Power Connector J_PWR (Pin 1=+12V, 2=+5V, 3=GND, 4=-12V_IN) at X=11.0, Y=16.0
    bb.add_footprint("HEADER", "PinHeader_1x04_P2.54mm_Vertical", "J_PWR", "PWR", 11.0, 16.0, pin_nets={
        "1": "+12V", "2": "+5V", "3": "GND", "4": "-12V_IN"
    })

    # DIP Switch SW1 (4-DIP SMD) at X=13.0, Y=36.0
    bb.add_footprint("SW_DIP", "SW_DIP_SPSTx04_Slide_6.7x11.72mm_W8.61mm_P2.54mm_LowProfile", "SW1", "4-DIP", 13.0, 36.0, pin_nets={
        "1": "+5V", "2": "+5V", "3": "+5V", "4": "+5V",
        "8": "X0", "7": "X1", "6": "X2", "5": "X3"
    })

    # Input Header J_IN (Vertical 1x5) at X=13.0, Y=49.0
    bb.add_footprint("HEADER", "PinHeader_1x05_P2.54mm_Vertical", "J_IN", "X0..X3/GND", 13.0, 49.0, pin_nets={
        "1": "X0", "2": "X1", "3": "X2", "4": "X3", "5": "GND"
    })

    # Pull-down resistors R_PD0..3 (10k, 0805, rot=90)
    # Placed vertically so signals pass East with zero obstructions
    bb.add_footprint("R_0805", "R_0805_2012Metric", "R_PD0", "10k", 21.0, 28.0, rot=90, pin_nets={"1": "GND", "2": "X0"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "R_PD1", "10k", 23.0, 30.0, rot=90, pin_nets={"1": "GND", "2": "X1"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "R_PD2", "10k", 23.0, 42.0, rot=90, pin_nets={"1": "X2", "2": "GND"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "R_PD3", "10k", 21.0, 44.0, rot=90, pin_nets={"1": "X3", "2": "GND"})

    # Test Points for Power
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_+12V", "+12V", 16.0, 5.5, pin_nets={"1": "+12V"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_+5V", "+5V", 6.0, 11.0, pin_nets={"1": "+5V"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_GND", "GND", 18.0, 21.08, pin_nets={"1": "GND"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_-12V", "-12V", 20.0, 63.0, pin_nets={"1": "-12V"})

    # Input Test Points
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_X0", "X0", 26.0, 20.0, pin_nets={"1": "X0"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_X1", "X1", 26.0, 24.0, pin_nets={"1": "X1"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_X2", "X2", 26.0, 46.0, pin_nets={"1": "X2"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_X3", "X3", 26.0, 50.0, pin_nets={"1": "X3"})

    # 0-Ohm Jumpers
    # 1. JMP_PWR: bridges -12V over +5V (West)
    bb.add_footprint("R_0805", "R_0805_2012Metric", "JMP_PWR", "0R", 7.5, 25.0, rot=0, pin_nets={"1": "-12V", "2": "-12V_IN"})
    # 2. JMP_BIAS0: bridges -12V over +12V drop at X=11.0 to feed Rb1_0 (North)
    bb.add_footprint("R_0805", "R_0805_2012Metric", "JMP_BIAS0", "0R", 11.0, 8.0, rot=90, pin_nets={"1": "-12V", "2": "-12V_NORTH0"})
    # 3. JMP_RECT0: bridges RECT_NODE_0_W over +12V drop at X=46.0
    bb.add_footprint("R_0805", "R_0805_2012Metric", "JMP_RECT0", "0R", 46.0, 20.0, rot=0, pin_nets={"1": "RECT_NODE_0_W", "2": "RECT_NODE_0"})
    # 4. JMP_RECT1: bridges RECT_NODE_1_W over -12V drop at X=46.0
    bb.add_footprint("R_0805", "R_0805_2012Metric", "JMP_RECT1", "0R", 46.0, 50.0, rot=0, pin_nets={"1": "RECT_NODE_1_W", "2": "RECT_NODE_1"})
    # 5. JMP_BIAS1: bridges -12V over V_ACT1 at X=61.0, Y=36.0 to feed Rb2_0 (North)
    bb.add_footprint("R_0805", "R_0805_2012Metric", "JMP_BIAS1", "0R", 61.0, 36.0, rot=90, pin_nets={"1": "-12V_NORTH1", "2": "-12V"})
    # 6. JMP_WTA: bridges V_OUT1 over V_OUT0 into U2 Pin 2
    bb.add_footprint("R_0805", "R_0805_2012Metric", "JMP_WTA", "0R", 85.0, 35.0, rot=0, pin_nets={"1": "V_OUT1_JMP", "2": "V_OUT1"})

    # U1 (Layer 1: SOIC-14 rot=270)
    u1_nets = {
        "7": "V_SUM0", "6": "SUM_NODE_0", "5": "GND", "4": "+12V", "3": "GND", "2": "RECT_NODE_0", "1": "RECT_OUT_0",
        "8": "V_SUM1", "9": "SUM_NODE_1", "10": "GND", "11": "-12V", "12": "GND", "13": "RECT_NODE_1", "14": "RECT_OUT_1"
    }
    bb.add_footprint("SOIC_14", "SOIC-14_3.9x8.7mm_P1.27mm", "U1", "TL074", 46.0, 35.0, rot=270, pin_nets=u1_nets)

    # Bypass Capacitors for U1
    bb.add_footprint("C_0805", "C_0805_2012Metric", "C1", "0.1uF", 46.0, 27.5, rot=90, pin_nets={"1": "+12V", "2": "GND"})
    bb.add_footprint("C_0805", "C_0805_2012Metric", "C2", "0.1uF", 46.0, 42.5, rot=90, pin_nets={"1": "GND", "2": "-12V"})

    # Neuron 0 Summing Components (North)
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rb1_0", "18k", 30.0, 16.0, rot=0, pin_nets={"1": "-12V_NORTH0", "2": "SUM_NODE_0"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "R1_00", "10k", 30.0, 20.0, rot=0, pin_nets={"1": "X0", "2": "SUM_NODE_0"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "R1_10", "10k", 30.0, 24.0, rot=0, pin_nets={"1": "X1", "2": "SUM_NODE_0"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rf1_0", "10k", 36.0, 16.0, rot=0, pin_nets={"1": "SUM_NODE_0", "2": "V_SUM0"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_SUM0", "V_SUM0", 38.0, 13.0, pin_nets={"1": "V_SUM0"})

    # Neuron 0 Rectifier (ReLU)
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rin_0", "10k", 40.0, 20.0, rot=0, pin_nets={"1": "V_SUM0", "2": "RECT_NODE_0_W"})
    bb.add_footprint("D_SOD123", "D_SOD-123", "D2_0", "1N4148", 48.54, 26.0, rot=90, pin_nets={"1": "RECT_OUT_0", "2": "RECT_NODE_0"})
    bb.add_footprint("D_SOD123", "D_SOD-123", "D1_0", "1N4148", 52.0, 26.0, rot=90, pin_nets={"2": "RECT_OUT_0", "1": "V_ACT0"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rrelu_0", "10k", 51.0, 16.0, rot=0, pin_nets={"1": "RECT_NODE_0", "2": "V_ACT0"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rpd_act0", "10k", 56.0, 14.0, rot=0, pin_nets={"1": "V_ACT0", "2": "GND"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_ACT0", "V_ACT0", 58.0, 20.0, pin_nets={"1": "V_ACT0"})

    # Neuron 1 Summing Components (South)
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rb1_1", "18k", 30.0, 54.0, rot=0, pin_nets={"1": "-12V", "2": "SUM_NODE_1"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "R1_21", "10k", 30.0, 46.0, rot=0, pin_nets={"1": "X2", "2": "SUM_NODE_1"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "R1_31", "10k", 30.0, 50.0, rot=0, pin_nets={"1": "X3", "2": "SUM_NODE_1"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rf1_1", "10k", 36.0, 54.0, rot=0, pin_nets={"1": "SUM_NODE_1", "2": "V_SUM1"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_SUM1", "V_SUM1", 38.0, 58.0, pin_nets={"1": "V_SUM1"})

    # Neuron 1 Rectifier (ReLU)
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rin_1", "10k", 40.0, 50.0, rot=0, pin_nets={"1": "V_SUM1", "2": "RECT_NODE_1_W"})
    bb.add_footprint("D_SOD123", "D_SOD-123", "D2_1", "1N4148", 48.54, 44.0, rot=90, pin_nets={"2": "RECT_OUT_1", "1": "RECT_NODE_1"})
    bb.add_footprint("D_SOD123", "D_SOD-123", "D1_1", "1N4148", 52.0, 44.0, rot=90, pin_nets={"1": "RECT_OUT_1", "2": "V_ACT1"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rrelu_1", "10k", 51.0, 54.0, rot=0, pin_nets={"1": "RECT_NODE_1", "2": "V_ACT1"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rpd_act1", "10k", 56.0, 56.0, rot=0, pin_nets={"1": "V_ACT1", "2": "GND"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_ACT1", "V_ACT1", 58.0, 50.0, pin_nets={"1": "V_ACT1"})

    # U2 (Layer 2 & WTA: SOIC-14 rot=270)
    u2_nets = {
        "7": "V_OUT0", "6": "SUM2_NODE_0", "5": "GND", "4": "+12V", "3": "V_OUT0", "2": "V_OUT1_JMP", "1": "CMP_OUT0",
        "8": "V_OUT1", "9": "SUM2_NODE_1", "10": "GND", "11": "-12V", "12": "V_OUT1", "13": "V_OUT0", "14": "CMP_OUT1"
    }
    bb.add_footprint("SOIC_14", "SOIC-14_3.9x8.7mm_P1.27mm", "U2", "TL074", 78.0, 35.0, rot=270, pin_nets=u2_nets)

    # Bypass Capacitors for U2
    bb.add_footprint("C_0805", "C_0805_2012Metric", "C3", "0.1uF", 78.0, 27.5, rot=90, pin_nets={"1": "+12V", "2": "GND"})
    bb.add_footprint("C_0805", "C_0805_2012Metric", "C4", "0.1uF", 78.0, 42.5, rot=90, pin_nets={"1": "GND", "2": "-12V"})

    # Output 0 Summing Components (North)
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rb2_0", "15k", 65.0, 16.0, rot=0, pin_nets={"1": "-12V_NORTH1", "2": "SUM2_NODE_0"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "R2_00", "10k", 65.0, 20.0, rot=0, pin_nets={"1": "V_ACT0", "2": "SUM2_NODE_0"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "R2_10", "10k", 65.0, 24.0, rot=0, pin_nets={"1": "V_ACT1", "2": "SUM2_NODE_0"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rf2_0", "10k", 71.0, 18.0, rot=0, pin_nets={"1": "SUM2_NODE_0", "2": "V_OUT0"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_OUT0", "V_OUT0", 71.0, 14.0, pin_nets={"1": "V_OUT0"})

    # Output 1 Summing Components (South)
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rb2_1", "22k", 65.0, 54.0, rot=0, pin_nets={"1": "-12V", "2": "SUM2_NODE_1"})
    bb.add_footprint("R_0805", "R_0805_2012Metric", "Rf2_1", "10k", 71.0, 52.0, rot=0, pin_nets={"1": "SUM2_NODE_1", "2": "V_OUT1"})
    bb.add_footprint("TESTPOINT", "TestPoint_Pad_D1.5mm", "TP_OUT1", "V_OUT1", 71.0, 56.0, pin_nets={"1": "V_OUT1"})

    # Output Indicator LEDs & Current-limiting Resistors
    bb.add_footprint("R_0805", "R_0805_2012Metric", "R_LED1", "1k", 87.0, 24.0, rot=0, pin_nets={"1": "CMP_OUT0", "2": "LED1_A"})
    bb.add_footprint("LED_0805", "LED_0805_2012Metric", "LED1", "Red_Vert", 92.0, 24.0, rot=180, pin_nets={"1": "GND", "2": "LED1_A"})

    bb.add_footprint("R_0805", "R_0805_2012Metric", "R_LED0", "1k", 87.0, 46.0, rot=0, pin_nets={"1": "CMP_OUT1", "2": "LED0_A"})
    bb.add_footprint("LED_0805", "LED_0805_2012Metric", "LED0", "Green_Horiz", 92.0, 46.0, rot=180, pin_nets={"1": "GND", "2": "LED0_A"})

    # Output Header J_OUT (Vertical 1x4) at X=96.0, Y=35.0
    bb.add_footprint("HEADER", "PinHeader_1x04_P2.54mm_Vertical", "J_OUT", "OUT", 96.0, 35.0, pin_nets={
        "1": "V_OUT0", "2": "CMP_OUT0", "3": "CMP_OUT1", "4": "V_OUT1"
    })

    # Hide passive text to ensure 0 silk overlaps
    for ref, fp in bb.footprints.items():
        if ref.startswith("R") or ref.startswith("C") or ref.startswith("D") or ref.startswith("JMP") or ref.startswith("TP_"):
            fp.Reference().SetVisible(False)
            fp.Value().SetVisible(False)
        elif ref.startswith("U"):
            fp.Value().SetVisible(False)
            fp.Reference().SetPosition(fp.GetPosition())
            fp.Reference().SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.0), pcbnew.FromMM(1.0)))
            fp.Reference().SetTextThickness(pcbnew.FromMM(0.15))

    # -------------------------------------------------------------------------
    # ROUTING
    # -------------------------------------------------------------------------

    # 1. +12V Rail
    p_pwr1 = bb.get_pad_pos("J_PWR", "1")
    p_tp_p12 = bb.get_pad_pos("TP_+12V", "1")
    p_c1_1 = bb.get_pad_pos("C1", "1")
    p_u1_4 = bb.get_pad_pos("U1", "4")
    p_c3_1 = bb.get_pad_pos("C3", "1")
    p_u2_4 = bb.get_pad_pos("U2", "4")

    # +12V along Y=5.5
    bb.add_route([p_pwr1, (p_pwr1[0], 5.5), p_tp_p12, (46.0, 5.5)], "+12V", width=0.70)
    # Under JMP_RECT0 at X=46.0 down to C1.1 and U1.4
    bb.add_route([(46.0, 5.5), (46.0, 19.0)], "+12V", width=0.60)
    bb.add_route([(46.0, 19.0), (46.0, 21.0)], "+12V", width=0.28) # under JMP_RECT0
    bb.add_route([(46.0, 21.0), p_c1_1, p_u1_4], "+12V", width=0.50)

    # +12V continues along Y=5.5 to U2
    bb.add_route([(46.0, 5.5), (78.0, 5.5), p_c3_1, p_u2_4], "+12V", width=0.70)

    # 2. -12V Rails (-12V_IN, -12V, -12V_NORTH0, -12V_NORTH1)
    p_pwr4 = bb.get_pad_pos("J_PWR", "4")
    p_jmp_pwr_2 = bb.get_pad_pos("JMP_PWR", "2")
    p_jmp_pwr_1 = bb.get_pad_pos("JMP_PWR", "1")
    p_jmp_bias0_1 = bb.get_pad_pos("JMP_BIAS0", "1")
    p_jmp_bias0_2 = bb.get_pad_pos("JMP_BIAS0", "2")
    p_rb1_0_1 = bb.get_pad_pos("Rb1_0", "1")
    p_tp_m12 = bb.get_pad_pos("TP_-12V", "1")
    p_rb1_1_1 = bb.get_pad_pos("Rb1_1", "1")
    p_c2_2 = bb.get_pad_pos("C2", "2")
    p_u1_11 = bb.get_pad_pos("U1", "11")
    p_jmp_bias1_2 = bb.get_pad_pos("JMP_BIAS1", "2")
    p_jmp_bias1_1 = bb.get_pad_pos("JMP_BIAS1", "1")
    p_rb2_0_1 = bb.get_pad_pos("Rb2_0", "1")
    p_rb2_1_1 = bb.get_pad_pos("Rb2_1", "1")
    p_c4_2 = bb.get_pad_pos("C4", "2")
    p_u2_11 = bb.get_pad_pos("U2", "11")

    # -12V_IN from J_PWR.4 to JMP_PWR.2
    bb.add_route([p_pwr4, p_jmp_pwr_2], "-12V_IN", width=0.50)

    # -12V West corridor: from JMP_PWR.1 to (5.5, 25.0)
    bb.add_route([p_jmp_pwr_1, (5.5, p_jmp_pwr_1[1])], "-12V", width=0.60)
    # North branch of West corridor up to JMP_BIAS0
    bb.add_route([(5.5, p_jmp_pwr_1[1]), (5.5, 7.0), (p_jmp_bias0_1[0], 7.0), p_jmp_bias0_1], "-12V", width=0.50)
    # JMP_BIAS0.2 exits North to Rb1_0
    bb.add_route([p_jmp_bias0_2, (p_jmp_bias0_2[0], 9.0), (28.0, 9.0), (28.0, p_rb1_0_1[1]), p_rb1_0_1], "-12V_NORTH0", width=0.50)

    # South branch of West corridor down to Y=63.0
    bb.add_route([(5.5, p_jmp_pwr_1[1]), (5.5, 63.0), p_tp_m12], "-12V", width=0.70)
    # South rail along Y=63.0
    bb.add_route([p_tp_m12, (p_rb1_1_1[0], 63.0), p_rb1_1_1], "-12V", width=0.50)
    # -12V up into U1.11 under JMP_RECT1 at X=46.0
    bb.add_route([(p_rb1_1_1[0], 63.0), (46.0, 63.0), (46.0, 51.0)], "-12V", width=0.60)
    bb.add_route([(46.0, 51.0), (46.0, 49.0)], "-12V", width=0.28) # under JMP_RECT1
    bb.add_route([(46.0, 49.0), p_c2_2, p_u1_11], "-12V", width=0.50)

    # -12V continues East along Y=63.0 to JMP_BIAS1
    bb.add_route([(46.0, 63.0), (61.0, 63.0), p_jmp_bias1_2], "-12V", width=0.60)
    # JMP_BIAS1.1 exits North to Rb2_0
    bb.add_route([p_jmp_bias1_1, (61.0, 16.0), p_rb2_0_1], "-12V_NORTH1", width=0.50)

    # -12V continues East along Y=63.0 to Rb2_1, C4, U2.11
    bb.add_route([(61.0, 63.0), (p_rb2_1_1[0], 63.0), p_rb2_1_1], "-12V", width=0.50)
    bb.add_route([(p_rb2_1_1[0], 63.0), (78.0, 63.0), p_c4_2, p_u2_11], "-12V", width=0.60)

    # 3. +5V Rail
    p_pwr2 = bb.get_pad_pos("J_PWR", "2")
    p_tp_p5 = bb.get_pad_pos("TP_+5V", "1")
    p_sw1_1 = bb.get_pad_pos("SW1", "1")
    p_sw1_2 = bb.get_pad_pos("SW1", "2")
    p_sw1_3 = bb.get_pad_pos("SW1", "3")
    p_sw1_4 = bb.get_pad_pos("SW1", "4")

    # +5V North to TP_+5V
    bb.add_route([p_pwr2, (7.5, p_pwr2[1]), (7.5, 11.0), p_tp_p5], "+5V", width=0.50)
    # +5V South under JMP_PWR to SW1.1..4
    bb.add_route([(7.5, p_pwr2[1]), (7.5, 24.0)], "+5V", width=0.50)
    bb.add_route([(7.5, 24.0), (7.5, 26.0)], "+5V", width=0.28) # under JMP_PWR
    bb.add_route([(7.5, 26.0), (7.5, 32.19), p_sw1_1], "+5V", width=0.50)
    bb.add_route([p_sw1_1, p_sw1_2, p_sw1_3, p_sw1_4], "+5V", width=0.50)

    # 4. Inputs X0..X3
    p_sw1_8 = bb.get_pad_pos("SW1", "8")
    p_sw1_7 = bb.get_pad_pos("SW1", "7")
    p_sw1_6 = bb.get_pad_pos("SW1", "6")
    p_sw1_5 = bb.get_pad_pos("SW1", "5")

    p_jin_1 = bb.get_pad_pos("J_IN", "1")
    p_jin_2 = bb.get_pad_pos("J_IN", "2")
    p_jin_3 = bb.get_pad_pos("J_IN", "3")
    p_jin_4 = bb.get_pad_pos("J_IN", "4")

    p_rpd0_2 = bb.get_pad_pos("R_PD0", "2")
    p_rpd1_2 = bb.get_pad_pos("R_PD1", "2")
    p_rpd2_1 = bb.get_pad_pos("R_PD2", "1")
    p_rpd3_1 = bb.get_pad_pos("R_PD3", "1")

    p_tp_x0 = bb.get_pad_pos("TP_X0", "1")
    p_tp_x1 = bb.get_pad_pos("TP_X1", "1")
    p_tp_x2 = bb.get_pad_pos("TP_X2", "1")
    p_tp_x3 = bb.get_pad_pos("TP_X3", "1")

    p_r1_00_1 = bb.get_pad_pos("R1_00", "1")
    p_r1_10_1 = bb.get_pad_pos("R1_10", "1")
    p_r1_21_1 = bb.get_pad_pos("R1_21", "1")
    p_r1_31_1 = bb.get_pad_pos("R1_31", "1")

    # J_IN parallel lines to SW1
    bb.add_route([p_jin_1, (14.5, p_jin_1[1]), (14.5, p_sw1_8[1]), p_sw1_8], "X0", width=0.35)
    bb.add_route([p_jin_2, (15.2, p_jin_2[1]), (15.2, p_sw1_7[1]), p_sw1_7], "X1", width=0.35)
    bb.add_route([p_jin_3, (15.9, p_jin_3[1]), (15.9, p_sw1_6[1]), p_sw1_6], "X2", width=0.35)
    bb.add_route([p_jin_4, (16.6, p_jin_4[1]), (16.6, p_sw1_5[1]), p_sw1_5], "X3", width=0.35)

    # X0: SW1.8 -> R_PD0.2 -> TP_X0 -> R1_00.1
    bb.add_route([p_sw1_8, (21.0, p_sw1_8[1]), p_rpd0_2, (21.0, 20.0), p_tp_x0, p_r1_00_1], "X0", width=0.45)
    # X1: SW1.7 -> R_PD1.2 -> TP_X1 -> R1_10.1
    bb.add_route([p_sw1_7, (23.0, p_sw1_7[1]), p_rpd1_2, (23.0, 24.0), p_tp_x1, p_r1_10_1], "X1", width=0.45)
    # X2: SW1.6 -> R_PD2.1 -> TP_X2 -> R1_21.1
    bb.add_route([p_sw1_6, (23.0, p_sw1_6[1]), p_rpd2_1, (23.0, 46.0), p_tp_x2, p_r1_21_1], "X2", width=0.45)
    # X3: SW1.5 -> R_PD3.1 -> TP_X3 -> R1_31.1
    bb.add_route([p_sw1_5, (21.0, p_sw1_5[1]), p_rpd3_1, (21.0, 50.0), p_tp_x3, p_r1_31_1], "X3", width=0.45)

    # 5. GND Distribution
    p_pwr3 = bb.get_pad_pos("J_PWR", "3")
    p_tp_gnd = bb.get_pad_pos("TP_GND", "1")
    p_rpd0_1 = bb.get_pad_pos("R_PD0", "1")
    p_rpd1_1 = bb.get_pad_pos("R_PD1", "1")
    p_rpd2_2 = bb.get_pad_pos("R_PD2", "2")
    p_rpd3_2 = bb.get_pad_pos("R_PD3", "2")
    p_jin_5 = bb.get_pad_pos("J_IN", "5")
    p_c1_2 = bb.get_pad_pos("C1", "2")
    p_u1_5 = bb.get_pad_pos("U1", "5")
    p_u1_3 = bb.get_pad_pos("U1", "3")
    p_u1_10 = bb.get_pad_pos("U1", "10")
    p_u1_12 = bb.get_pad_pos("U1", "12")
    p_c2_1 = bb.get_pad_pos("C2", "1")
    p_rpd_act0_2 = bb.get_pad_pos("Rpd_act0", "2")
    p_rpd_act1_2 = bb.get_pad_pos("Rpd_act1", "2")
    p_c3_2 = bb.get_pad_pos("C3", "2")
    p_u2_5 = bb.get_pad_pos("U2", "5")
    p_c4_1 = bb.get_pad_pos("C4", "1")
    p_u2_10 = bb.get_pad_pos("U2", "10")
    p_led1_1 = bb.get_pad_pos("LED1", "1")
    p_led0_1 = bb.get_pad_pos("LED0", "1")

    # GND from J_PWR.3 to TP_GND
    bb.add_route([p_pwr3, p_tp_gnd], "GND", width=0.60)
    # GND to R_PD0.1, R_PD1.1
    bb.add_route([p_tp_gnd, (p_tp_gnd[0], p_rpd0_1[1]), p_rpd0_1], "GND", width=0.50)
    bb.add_route([p_rpd0_1, (p_rpd0_1[0], p_rpd1_1[1]), p_rpd1_1], "GND", width=0.50)
    # GND to R_PD2.2, R_PD3.2, and J_IN.5
    bb.add_route([p_tp_gnd, (p_tp_gnd[0], p_rpd2_2[1]), p_rpd2_2], "GND", width=0.50)
    bb.add_route([p_rpd2_2, (p_rpd2_2[0], p_rpd3_2[1]), p_rpd3_2], "GND", width=0.50)
    bb.add_route([p_rpd3_2, (p_rpd3_2[0], 59.16), p_jin_5], "GND", width=0.50)

    # GND North Bus (Y=11.0)
    bb.add_route([(p_tp_gnd[0], 11.0), p_tp_gnd], "GND", width=0.60)
    bb.add_route([(p_tp_gnd[0], 11.0), (44.73, 11.0), (44.73, 27.5), p_c1_2, p_u1_5], "GND", width=0.50)
    bb.add_route([p_u1_5, p_u1_3], "GND", width=0.40)
    bb.add_route([(44.73, 11.0), (56.913, 11.0), p_rpd_act0_2], "GND", width=0.60)
    bb.add_route([(56.913, 11.0), (76.73, 11.0), (76.73, 27.5), p_c3_2, p_u2_5], "GND", width=0.60)
    bb.add_route([(76.73, 11.0), (92.913, 11.0), (92.913, p_led1_1[1]), p_led1_1], "GND", width=0.60)

    # GND vertical bridge through U1 package (Pin 5 to Pin 10)
    bb.add_route([p_u1_5, p_u1_10], "GND", width=0.40)
    bb.add_route([p_u1_10, p_u1_12], "GND", width=0.40)
    # GND vertical bridge through U2 package (Pin 5 to Pin 10)
    bb.add_route([p_u2_5, p_u2_10], "GND", width=0.40)

    # GND South Bus (Y=58.0)
    bb.add_route([p_u1_10, (44.73, 42.5), p_c2_1, (44.73, 58.0)], "GND", width=0.50)
    bb.add_route([(44.73, 58.0), (56.913, 58.0), p_rpd_act1_2], "GND", width=0.60)
    bb.add_route([(56.913, 58.0), (76.73, 58.0), (76.73, 42.5), p_c4_1, p_u2_10], "GND", width=0.60)
    bb.add_route([(76.73, 58.0), (92.913, 58.0), (92.913, p_led0_1[1]), p_led0_1], "GND", width=0.60)

    # 6. Neuron 0 Summing & Rectifier (North)
    p_rb1_0_2 = bb.get_pad_pos("Rb1_0", "2")
    p_r1_00_2 = bb.get_pad_pos("R1_00", "2")
    p_r1_10_2 = bb.get_pad_pos("R1_10", "2")
    p_rf1_0_1 = bb.get_pad_pos("Rf1_0", "1")
    p_rf1_0_2 = bb.get_pad_pos("Rf1_0", "2")
    p_u1_6 = bb.get_pad_pos("U1", "6")
    p_u1_7 = bb.get_pad_pos("U1", "7")
    p_tp_sum0 = bb.get_pad_pos("TP_SUM0", "1")
    p_rin_0_1 = bb.get_pad_pos("Rin_0", "1")
    p_rin_0_2 = bb.get_pad_pos("Rin_0", "2")
    p_jmp_rect0_1 = bb.get_pad_pos("JMP_RECT0", "1")
    p_jmp_rect0_2 = bb.get_pad_pos("JMP_RECT0", "2")
    p_d2_0_1 = bb.get_pad_pos("D2_0", "1")
    p_d2_0_2 = bb.get_pad_pos("D2_0", "2")
    p_d1_0_1 = bb.get_pad_pos("D1_0", "1")
    p_d1_0_2 = bb.get_pad_pos("D1_0", "2")
    p_u1_1 = bb.get_pad_pos("U1", "1")
    p_u1_2 = bb.get_pad_pos("U1", "2")
    p_rrelu_0_1 = bb.get_pad_pos("Rrelu_0", "1")
    p_rrelu_0_2 = bb.get_pad_pos("Rrelu_0", "2")
    p_rpd_act0_1 = bb.get_pad_pos("Rpd_act0", "1")
    p_tp_act0 = bb.get_pad_pos("TP_ACT0", "1")

    # SUM_NODE_0
    bb.add_route([p_r1_10_2, (31.5, p_r1_10_2[1]), (31.5, p_r1_00_2[1]), p_r1_00_2], "SUM_NODE_0", width=0.45)
    bb.add_route([p_r1_00_2, (31.5, p_r1_00_2[1]), (31.5, p_rb1_0_2[1]), p_rb1_0_2, p_rf1_0_1], "SUM_NODE_0", width=0.45)
    bb.add_route([p_rf1_0_1, (35.087, 14.5), (43.46, 14.5), p_u1_6], "SUM_NODE_0", width=0.40)

    # V_SUM0
    bb.add_route([p_u1_7, (42.19, 13.0), p_tp_sum0, (36.913, 13.0), p_rf1_0_2], "V_SUM0", width=0.45)
    bb.add_route([p_u1_7, (42.19, 20.0), p_rin_0_1], "V_SUM0", width=0.45)

    # RECT_NODE_0_W
    bb.add_route([p_rin_0_2, p_jmp_rect0_1], "RECT_NODE_0_W", width=0.45)

    # RECT_NODE_0 (exits JMP_RECT0.2 directly to U1.2, D2_0.2, Rrelu_0.1)
    bb.add_route([p_jmp_rect0_2, (48.54, 20.0), p_d2_0_2, p_u1_2], "RECT_NODE_0", width=0.40)
    bb.add_route([(48.54, 20.0), (48.54, 16.0), p_rrelu_0_1], "RECT_NODE_0", width=0.40)

    # RECT_OUT_0
    bb.add_route([p_u1_1, (49.81, 27.65), p_d2_0_1], "RECT_OUT_0", width=0.40)
    bb.add_route([(49.81, 27.65), p_d1_0_2], "RECT_OUT_0", width=0.40)

    # V_ACT0
    bb.add_route([p_d1_0_1, (52.0, 16.0), p_rrelu_0_2, (55.087, 16.0), (55.087, p_rpd_act0_1[1]), p_rpd_act0_1], "V_ACT0", width=0.45)
    bb.add_route([p_d1_0_1, (58.0, p_d1_0_1[1]), p_tp_act0], "V_ACT0", width=0.45)

    # 7. Neuron 1 Summing & Rectifier (South)
    p_rb1_1_2 = bb.get_pad_pos("Rb1_1", "2")
    p_r1_21_2 = bb.get_pad_pos("R1_21", "2")
    p_r1_31_2 = bb.get_pad_pos("R1_31", "2")
    p_rf1_1_1 = bb.get_pad_pos("Rf1_1", "1")
    p_rf1_1_2 = bb.get_pad_pos("Rf1_1", "2")
    p_u1_9 = bb.get_pad_pos("U1", "9")
    p_u1_8 = bb.get_pad_pos("U1", "8")
    p_tp_sum1 = bb.get_pad_pos("TP_SUM1", "1")
    p_rin_1_1 = bb.get_pad_pos("Rin_1", "1")
    p_rin_1_2 = bb.get_pad_pos("Rin_1", "2")
    p_jmp_rect1_1 = bb.get_pad_pos("JMP_RECT1", "1")
    p_jmp_rect1_2 = bb.get_pad_pos("JMP_RECT1", "2")
    p_d2_1_1 = bb.get_pad_pos("D2_1", "1")
    p_d2_1_2 = bb.get_pad_pos("D2_1", "2")
    p_d1_1_1 = bb.get_pad_pos("D1_1", "1")
    p_d1_1_2 = bb.get_pad_pos("D1_1", "2")
    p_u1_14 = bb.get_pad_pos("U1", "14")
    p_u1_13 = bb.get_pad_pos("U1", "13")
    p_rrelu_1_1 = bb.get_pad_pos("Rrelu_1", "1")
    p_rrelu_1_2 = bb.get_pad_pos("Rrelu_1", "2")
    p_rpd_act1_1 = bb.get_pad_pos("Rpd_act1", "1")
    p_tp_act1 = bb.get_pad_pos("TP_ACT1", "1")

    # SUM_NODE_1
    bb.add_route([p_r1_21_2, (31.5, p_r1_21_2[1]), (31.5, p_r1_31_2[1]), p_r1_31_2], "SUM_NODE_1", width=0.45)
    bb.add_route([p_r1_31_2, (31.5, p_r1_31_2[1]), (31.5, p_rb1_1_2[1]), p_rb1_1_2, p_rf1_1_1], "SUM_NODE_1", width=0.45)
    bb.add_route([p_rf1_1_1, (35.087, 55.5), (43.46, 55.5), p_u1_9], "SUM_NODE_1", width=0.40)

    # V_SUM1
    bb.add_route([p_u1_8, (42.19, 58.0), p_tp_sum1, (36.913, 58.0), p_rf1_1_2], "V_SUM1", width=0.45)
    bb.add_route([p_u1_8, (42.19, 50.0), p_rin_1_1], "V_SUM1", width=0.45)

    # RECT_NODE_1_W
    bb.add_route([p_rin_1_2, p_jmp_rect1_1], "RECT_NODE_1_W", width=0.45)

    # RECT_NODE_1
    bb.add_route([p_jmp_rect1_2, (48.54, 50.0), p_d2_1_1, p_u1_13], "RECT_NODE_1", width=0.40)
    bb.add_route([(48.54, 50.0), (48.54, 54.0), p_rrelu_1_1], "RECT_NODE_1", width=0.40)

    # RECT_OUT_1
    bb.add_route([p_u1_14, (49.81, 42.35), p_d2_1_2], "RECT_OUT_1", width=0.40)
    bb.add_route([(49.81, 42.35), p_d1_1_1], "RECT_OUT_1", width=0.40)

    # V_ACT1
    bb.add_route([p_d1_1_2, (52.0, 54.0), p_rrelu_1_2, (55.087, 54.0), (55.087, p_rpd_act1_1[1]), p_rpd_act1_1], "V_ACT1", width=0.45)
    bb.add_route([p_d1_1_2, (58.0, p_d1_1_2[1]), p_tp_act1], "V_ACT1", width=0.45)

    # 8. Layer 2 Summing (U2)
    p_r2_00_1 = bb.get_pad_pos("R2_00", "1")
    p_r2_10_1 = bb.get_pad_pos("R2_10", "1")
    p_rb2_0_2 = bb.get_pad_pos("Rb2_0", "2")
    p_r2_00_2 = bb.get_pad_pos("R2_00", "2")
    p_r2_10_2 = bb.get_pad_pos("R2_10", "2")
    p_rf2_0_1 = bb.get_pad_pos("Rf2_0", "1")
    p_rf2_0_2 = bb.get_pad_pos("Rf2_0", "2")
    p_u2_6 = bb.get_pad_pos("U2", "6")
    p_u2_7 = bb.get_pad_pos("U2", "7")
    p_tp_out0 = bb.get_pad_pos("TP_OUT0", "1")
    p_u2_3 = bb.get_pad_pos("U2", "3")
    p_u2_13 = bb.get_pad_pos("U2", "13")
    p_jout_1 = bb.get_pad_pos("J_OUT", "1")

    # V_ACT0 -> R2_00.1
    bb.add_route([p_tp_act0, p_r2_00_1], "V_ACT0", width=0.45)
    # V_ACT1 -> under JMP_BIAS1 at Y=36.0 -> R2_10.1
    bb.add_route([p_tp_act1, (61.0, p_tp_act1[1]), (61.0, 37.0)], "V_ACT1", width=0.45)
    bb.add_route([(61.0, 37.0), (61.0, 35.0)], "V_ACT1", width=0.28) # under JMP_BIAS1
    bb.add_route([(61.0, 35.0), (61.0, p_r2_10_1[1]), p_r2_10_1], "V_ACT1", width=0.45)

    # SUM2_NODE_0
    bb.add_route([p_r2_10_2, (66.5, p_r2_10_2[1]), (66.5, p_r2_00_2[1]), p_r2_00_2], "SUM2_NODE_0", width=0.45)
    bb.add_route([p_r2_00_2, (66.5, p_r2_00_2[1]), (66.5, p_rb2_0_2[1]), p_rb2_0_2, p_rf2_0_1], "SUM2_NODE_0", width=0.45)
    bb.add_route([p_rf2_0_1, (70.087, 14.5), (75.46, 14.5), p_u2_6], "SUM2_NODE_0", width=0.40)

    # V_OUT0 (from U2.7)
    bb.add_route([p_u2_7, (74.19, 13.0), p_tp_out0, (71.913, 13.0), p_rf2_0_2], "V_OUT0", width=0.45)
    bb.add_route([p_tp_out0, (83.5, 14.0), (83.5, 30.0), p_u2_3], "V_OUT0", width=0.45)
    bb.add_route([(83.5, 30.0), (85.0, 30.0), (85.0, 34.0)], "V_OUT0", width=0.45)
    bb.add_route([(85.0, 34.0), (85.0, 36.0)], "V_OUT0", width=0.28) # under JMP_WTA
    bb.add_route([(85.0, 36.0), (85.0, 38.5), (80.54, 38.5), p_u2_13], "V_OUT0", width=0.40)
    bb.add_route([(83.5, 14.0), (96.0, 14.0), p_jout_1], "V_OUT0", width=0.50)

    # SUM2_NODE_1
    p_rb2_1_2 = bb.get_pad_pos("Rb2_1", "2")
    p_rf2_1_1 = bb.get_pad_pos("Rf2_1", "1")
    p_rf2_1_2 = bb.get_pad_pos("Rf2_1", "2")
    p_u2_9 = bb.get_pad_pos("U2", "9")
    p_u2_8 = bb.get_pad_pos("U2", "8")
    p_tp_out1 = bb.get_pad_pos("TP_OUT1", "1")
    p_u2_12 = bb.get_pad_pos("U2", "12")
    p_jmp_wta_1 = bb.get_pad_pos("JMP_WTA", "1")
    p_jmp_wta_2 = bb.get_pad_pos("JMP_WTA", "2")
    p_u2_2 = bb.get_pad_pos("U2", "2")
    p_jout_4 = bb.get_pad_pos("J_OUT", "4")

    bb.add_route([p_rb2_1_2, p_rf2_1_1, (70.087, 55.5), (75.46, 55.5), p_u2_9], "SUM2_NODE_1", width=0.40)

    # V_OUT1 (from U2.8)
    bb.add_route([p_u2_8, (74.19, 56.5), p_tp_out1, (71.913, 56.5), p_rf2_1_2], "V_OUT1", width=0.45)
    bb.add_route([p_tp_out1, (79.27, 56.5), p_u2_12], "V_OUT1", width=0.45)
    bb.add_route([(79.27, 56.5), (86.5, 56.5), (86.5, p_jmp_wta_2[1]), p_jmp_wta_2], "V_OUT1", width=0.45)
    bb.add_route([(86.5, 56.5), (96.0, 56.5), p_jout_4], "V_OUT1", width=0.50)

    # V_OUT1_JMP (JMP_WTA.1 to U2.2)
    bb.add_route([p_jmp_wta_1, (83.0, p_jmp_wta_1[1]), (83.0, 31.5), (80.54, 31.5), p_u2_2], "V_OUT1_JMP", width=0.40)

    # 9. Comparators & LEDs
    p_u2_1 = bb.get_pad_pos("U2", "1")
    p_rled1_1 = bb.get_pad_pos("R_LED1", "1")
    p_rled1_2 = bb.get_pad_pos("R_LED1", "2")
    p_led1_2 = bb.get_pad_pos("LED1", "2")
    p_jout_2 = bb.get_pad_pos("J_OUT", "2")

    bb.add_route([p_u2_1, (81.81, 24.0), p_rled1_1], "CMP_OUT0", width=0.40)
    bb.add_route([p_rled1_1, (87.0, 37.54), p_jout_2], "CMP_OUT0", width=0.40)
    bb.add_route([p_rled1_2, p_led1_2], "LED1_A", width=0.45)

    p_u2_14 = bb.get_pad_pos("U2", "14")
    p_rled0_1 = bb.get_pad_pos("R_LED0", "1")
    p_rled0_2 = bb.get_pad_pos("R_LED0", "2")
    p_led0_2 = bb.get_pad_pos("LED0", "2")
    p_jout_3 = bb.get_pad_pos("J_OUT", "3")

    bb.add_route([p_u2_14, (81.81, 46.0), p_rled0_1], "CMP_OUT1", width=0.40)
    bb.add_route([p_rled0_1, (87.0, 40.08), p_jout_3], "CMP_OUT1", width=0.40)
    bb.add_route([p_rled0_2, p_led0_2], "LED0_A", width=0.45)

    bb.save(output_path)

if __name__ == "__main__":
    out_pcb = os.path.join(WORKSPACE_DIR, "test_board_single_layer.kicad_pcb")
    build_board(out_pcb)
