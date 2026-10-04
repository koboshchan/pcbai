import sys
import pcbnew

def verify_board(board_path):
    print(f"\n==========================================")
    print(f"VERIFYING BOARD RULES: {board_path}")
    print(f"==========================================")
    board = pcbnew.LoadBoard(board_path)
    
    # Check board bbox
    bbox = board.GetBoardEdgesBoundingBox()
    width_mm = pcbnew.ToMM(bbox.GetWidth())
    height_mm = pcbnew.ToMM(bbox.GetHeight())
    print(f"Board Bounding Box: {width_mm:.2f} mm x {height_mm:.2f} mm")
    
    # Check tracks
    b_cu_count = 0
    f_cu_count = 0
    other_layer_tracks = 0
    min_width = 999.0
    vias_count = 0
    
    for track in board.GetTracks():
        if isinstance(track, pcbnew.PCB_VIA):
            vias_count += 1
            continue
        layer_name = board.GetLayerName(track.GetLayer())
        w = pcbnew.ToMM(track.GetWidth())
        if w < min_width:
            min_width = w
        if layer_name == "B.Cu":
            b_cu_count += 1
        elif layer_name == "F.Cu":
            f_cu_count += 1
        else:
            other_layer_tracks += 1
            
    print(f"F.Cu tracks: {f_cu_count}")
    print(f"B.Cu tracks: {b_cu_count} (must be 0)")
    print(f"Other layer tracks: {other_layer_tracks} (must be 0)")
    print(f"Vias count: {vias_count} (must be 0)")
    print(f"Minimum trace width: {min_width:.3f} mm (must be >= 0.35 mm)")
    
    # Check footprints and jumpers
    jumpers = [fp for fp in board.GetFootprints() if fp.GetReference().startswith("W")]
    print(f"Total footprints: {len(board.GetFootprints())}")
    print(f"Total wire jumpers: {len(jumpers)}")
    
    passed = (b_cu_count == 0 and other_layer_tracks == 0 and vias_count == 0 and min_width >= 0.35)
    print(f"STATUS: {'PASS' if passed else 'FAIL'}")
    return passed

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "daughtercard1a_weights_l1.kicad_pcb"
    ok = verify_board(path)
    sys.exit(0 if ok else 1)
