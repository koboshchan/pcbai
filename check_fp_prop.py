import pcbnew
board = pcbnew.BOARD()
fp = pcbnew.FOOTPRINT(board)
fp.SetReference("R1")
fp.SetLibDescription("polarity=positive")
board.Add(fp)
board.Save("test_prop.kicad_pcb")
with open("test_prop.kicad_pcb") as f:
    text = f.read()
print("Contains Description property?", 'property "Description"' in text)
print("Contains polarity=positive?", "polarity=positive" in text)
