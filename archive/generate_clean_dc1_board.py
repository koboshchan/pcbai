import os
import pcbnew
import uuid

WORKSPACE_DIR = "/Users/lucaszhang/pcbai"
def mm(v): return int(v * 1000000)

def prepare_board(board_path):
    b = pcbnew.LoadBoard(board_path)
    # Remove existing tracks
    for t in list(b.GetTracks()):
        b.Delete(t)
    
    nets = {b.FindNet(i).GetNetname(): b.FindNet(i) for i in range(b.GetNetCount()) if b.FindNet(i)}
    net_gnd = nets["GND"]
    
    def add_track(x1, y1, x2, y2, layer, net, width=0.25):
        trk = pcbnew.PCB_TRACK(b)
        trk.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        trk.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        trk.SetWidth(mm(width))
        trk.SetLayer(layer)
        trk.SetNet(net)
        b.Add(trk)

    def add_via(x, y, net, size=0.50, drill=0.30):
        via = pcbnew.PCB_VIA(b)
        via.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        via.SetWidth(mm(size))
        via.SetDrill(mm(drill))
        via.SetNet(net)
        b.Add(via)

    # 1. Outward-facing GND vias for U1
    # Pin 3 at (52.3, 48.73)
    add_via(50.5, 48.73, net_gnd)
    add_track(52.3, 48.73, 50.5, 48.73, pcbnew.F_Cu, net_gnd)

    # Pin 5 at (52.3, 51.27)
    add_via(50.5, 51.27, net_gnd)
    add_track(52.3, 51.27, 50.5, 51.27, pcbnew.F_Cu, net_gnd)

    # Pin 10 at (57.7, 51.27)
    add_via(59.5, 51.27, net_gnd)
    add_track(57.7, 51.27, 59.5, 51.27, pcbnew.F_Cu, net_gnd)

    # Pin 12 at (57.7, 48.73)
    add_via(59.5, 48.73, net_gnd)
    add_track(57.7, 48.73, 59.5, 48.73, pcbnew.F_Cu, net_gnd)

    # C_U1P (52.0, 42.0), Pad 2 (GND) at (52.95, 42.0) -> via at (52.95, 43.5)
    add_via(52.95, 43.5, net_gnd)
    add_track(52.95, 42.0, 52.95, 43.5, pcbnew.F_Cu, net_gnd)

    # C_U1N (58.0, 58.0), Pad 2 (GND) at (58.95, 58.0) -> via at (58.95, 56.5)
    add_via(58.95, 56.5, net_gnd)
    add_track(58.95, 58.0, 58.95, 56.5, pcbnew.F_Cu, net_gnd)

    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    b.Save(board_path)
    print(f"Prepared clean board with GND vias: {board_path}")

if __name__ == "__main__":
    prepare_board("/Users/lucaszhang/pcbai/daughtercard1a_weights_l1.kicad_pcb")
