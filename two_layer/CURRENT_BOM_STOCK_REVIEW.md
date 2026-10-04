# Current BOM stock review

Checked 2026-10-04 against `two_layer/sourcing_inventory_provisional.json`. Research only. This report does not change a BOM, assembly map, PCB, schematic, model, or part assignment.

## Scope and readiness

The authoritative provisional inventory covers seven exact board files and has 1,249 items in 100 distinct value-plus-footprint groups. It contains 1,034 resistors and 215 non-resistor items. Of the non-resistor items, 17 are classified for manual assembly (including one L7805 regulator), 14 are mechanical mounting-hole features, and the remaining 184 are SMT electrical components. These classifications overlap for the manually assembled regulator. The current metadata assigns only eight Diodes C126402 shift registers, one Samsung C28323 1uF capacitor, and one ST C111887 regulator. The other 1,239 items have no LCSC code; 1,240 items are marked unverified. The inventory is provisional, not a released or fabrication-ready BOM.

The inventory does not encode resistor tolerance or wattage, nor the required tolerance for most passives. A nominal value and footprint alone are not enough to qualify a resistor. Exact catalog pages below are sourcing evidence, not authorization to map a part. Stock is a changing snapshot; a JLC catalog quantity is not a board quote or a completed assembly order.

## Resistors

All 80 groups below use `R_0805_2012Metric`. Every row is currently unassigned in the inventory. Unless specifically qualified in the following notes, no stable exact-part current quantity is established here; do not interpret that as out of stock. Confirm the required tolerance, power rating, voltage rating, and resistor technology before mapping any LCSC/JLC listing. Dedicated value searches returned incomplete or conflicting catalog results for many values, particularly the uncommon E96 values and 6.2M.

| Value | Qty | Status |
|---|---:|---|
| 0R | 1 | Unassigned; not qualified |
| 820 | 1 | Unassigned; not qualified |
| 1k | 10 | Unassigned; candidate evidence below |
| 8.66k | 1 | Unassigned; not qualified |
| 10k | 97 | Unassigned; candidate evidence below |
| 13k | 1 | Unassigned; not qualified |
| 14.3k | 2 | Unassigned; not qualified |
| 14.7k | 2 | Unassigned; not qualified |
| 15.4k | 1 | Unassigned; not qualified |
| 16.2k | 1 | Unassigned; not qualified |
| 17.4k | 1 | Unassigned; not qualified |
| 18.2k | 3 | Unassigned; not qualified |
| 20k | 1 | Unassigned; not qualified |
| 21k | 1 | Unassigned; not qualified |
| 22k | 20 | Unassigned; not qualified |
| 22.6k | 1 | Unassigned; not qualified |
| 24k | 1 | Unassigned; not qualified |
| 24.9k | 1 | Unassigned; not qualified |
| 27k | 3 | Unassigned; not qualified |
| 28k | 1 | Unassigned; not qualified |
| 29.4k | 1 | Unassigned; not qualified |
| 30k | 1 | Unassigned; not qualified |
| 33k | 4 | Unassigned; not qualified |
| 34k | 1 | Unassigned; not qualified |
| 35.7k | 2 | Unassigned; not qualified |
| 36k | 3 | Unassigned; not qualified |
| 39k | 6 | Unassigned; not qualified |
| 43k | 7 | Unassigned; not qualified |
| 47k | 8 | Unassigned; not qualified |
| 51k | 8 | Unassigned; not qualified |
| 52.3k | 1 | Unassigned; not qualified |
| 56k | 9 | Unassigned; not qualified |
| 61.9k | 2 | Unassigned; not qualified |
| 62k | 10 | Unassigned; not qualified |
| 68k | 14 | Unassigned; not qualified |
| 75k | 19 | Unassigned; not qualified |
| 82k | 17 | Unassigned; not qualified |
| 90.9k | 1 | Unassigned; not qualified |
| 91k | 25 | Unassigned; not qualified |
| 100k | 45 | Unassigned; candidate evidence below |
| 110k | 29 | Unassigned; not qualified |
| 113k | 1 | Unassigned; not qualified |
| 120k | 17 | Unassigned; not qualified |
| 130k | 25 | Unassigned; not qualified |
| 150k | 34 | Unassigned; not qualified |
| 160k | 38 | Unassigned; not qualified |
| 180k | 38 | Unassigned; not qualified |
| 200k | 43 | Unassigned; not qualified |
| 220k | 46 | Unassigned; candidate evidence below |
| 240k | 34 | Unassigned; not qualified |
| 270k | 46 | Unassigned; not qualified |
| 300k | 35 | Unassigned; not qualified |
| 330k | 41 | Unassigned; not qualified |
| 360k | 28 | Unassigned; not qualified |
| 390k | 24 | Unassigned; not qualified |
| 430k | 24 | Unassigned; not qualified |
| 470k | 25 | Unassigned; not qualified |
| 510k | 20 | Unassigned; not qualified |
| 560k | 21 | Unassigned; not qualified |
| 620k | 11 | Unassigned; not qualified |
| 680k | 16 | Unassigned; not qualified |
| 750k | 18 | Unassigned; not qualified |
| 820k | 11 | Unassigned; not qualified |
| 910k | 9 | Unassigned; not qualified |
| 1M | 10 | Unassigned; not qualified |
| 1.1M | 12 | Unassigned; candidate identity found; current catalog quantity not verified |
| 1.2M | 6 | Unassigned; not qualified |
| 1.3M | 7 | Unassigned; not qualified |
| 1.5M | 4 | Unassigned; not qualified |
| 1.6M | 4 | Unassigned; not qualified |
| 1.8M | 3 | Unassigned; not qualified |
| 2M | 8 | Unassigned; not qualified |
| 2.2M | 4 | Unassigned; not qualified |
| 2.4M | 1 | Unassigned; not qualified |
| 2.7M | 1 | Unassigned; not qualified |
| 3M | 1 | Unassigned; not qualified |
| 3.3M | 2 | Unassigned; not qualified |
| 3.9M | 1 | Unassigned; not qualified |
| 5.1M | 1 | Unassigned; not qualified |
| 6.2M | 1 | Unassigned; exact current LCSC/JLC item and orderable quantity not verified |

Catalog checks with usable exact-value evidence:

- **1k, qty 10:** YAGEO RC0805FR-071KL, LCSC [C95781](https://www.lcsc.com/product-detail/C95781.html), is 1kΩ, 0805, ±1%, 125mW. The LCSC page showed 3,087,500 in stock in the captured lookup. Tolerance is not specified by this inventory, so this is a candidate listing only, not an assigned part.
- **10k, qty 97:** UNI-ROYAL 0805W8F1002T5E, LCSC [C17414](https://www.lcsc.com/product-detail/Chip-Resistor-Surface-Mount_Uniroyal-Elec-0805W8F1002T5E_C17414.html), is 10kΩ, 0805, ±1%, 125mW. A JLC VO 0805 ±1% listing [C2889436](https://jlcpcb.com/partdetail/VO-0805_1_10K/C2889436) showed zero in stock and a minimum of 5,000, and therefore is not orderable from that listing in the observed snapshot. No current quantity was established for C17414.
- **100k, qty 45:** LCSC [C416061](https://www.lcsc.com/product-detail/C416061.html) identifies Viking CR-05FL7--100K, 100kΩ, 0805, ±1%, 125mW; the lookup did not capture a reliable current quantity. The JLC VO 0805 ±1% listing [C2889441](https://jlcpcb.com/partdetail/VO-0805_1_100K/C2889441) showed zero stock and minimum 4,478, so it was not orderable from that listing in the observed snapshot.
- **220k, qty 46:** LCSC [C2889548](https://www.lcsc.com/product-detail/C2889548.html) is VO 220kΩ ±5%, 0805, with 900 in stock in the captured listing. This does not establish suitability because the design tolerance is absent. Do not assign it without confirming tolerance is acceptable.
- **1.1M, qty 12:** Panasonic ERJ-6ENF1104V was identified as an exact 1.1MΩ, 0805, ±1% part through distributor search, but a current LCSC/JLC orderable quantity was not verified. It remains unassigned.

For the other resistor values, current exact-value part codes and usable orderable quantities remain unverified. This includes 6.2M qty 1 and the uncommon one-off E96 values. Absence of a verified result is not evidence that a part is unavailable. No resistor substitute or tolerance assumption is selected here.

## Other electrical and mechanical groups

The groups below complete the inventory coverage. Counts are board-item quantities, not necessarily the minimum purchasable quantity. “Not qualified” means the current inventory has no assigned exact source or no sufficiently matched catalog result; it does not mean unavailable.

| Value | Footprint | Qty | Catalog / status |
|---|---|---:|---|
| 0.1uF | `C_0805_2012Metric` | 41 | Unassigned. Exact matching YAGEO CC0805KRX7R9BB104, LCSC [C49678](https://www.lcsc.com/product-detail/C49678.html), 100nF, 50V, X7R, ±10%, 0805. LCSC page showed 9,147,800 in stock. A JLC stock/orderable snapshot from the catalog review was 19,171,525 / 16,463,004; these are dynamic catalogue quantities, not a project quote. No assignment made. |
| 1uF | `C_0805_2012Metric` | 65 | One item is mapped to Samsung CL21B105KBFNNNE, LCSC/JLC [C28323](https://www.lcsc.com/product-detail/C28323.html) / [JLC listing](https://jlcpcb.com/partdetail/29074-CL21B105KBFNNNE/C28323), 1uF, 50V, X7R, ±10%, 0805; 64 remain unassigned. The inventory's C28323 stock check was 2,228,988 LCSC / 1,499,417 JLC available to order at 07:49:15 UTC. Later search results conflict: the LCSC product page appeared both out of stock and with a separate stock snapshot of 271,630; the current JLC page confirms specification and SMT assembly support but did not expose a reliable quantity. Treat present availability as **conflicted, recheck before order**. No guaranteed effective capacitance at 15.75V is established. |
| 100uF | `CP_Elec_8x10` | 2 | Exact Panasonic EEE-FK1H101P, LCSC [C178548](https://www.lcsc.com/product-detail/Aluminum-Electrolytic-Capacitors-SMD_PANASONIC-EEEFK1H101P_C178548.html) / [JLC listing](https://jlcpcb.com/partdetail/PANASONIC-EEEFK1H101P/C178548): 100uF, 50V, ±20%, SMD D8xL10.2mm, body diameter 8mm. LCSC showed 4,936 in stock; a JLC snapshot showed 4,936 in stock / 4,547 available to order. This matches the named value, voltage, tolerance, and package size. |
| 10uF | `CP_Elec_5x5.8` | 1 | Unassigned; no verified exact footprint match. LCSC [C970654](https://www.lcsc.com/product-detail/C970654.html) is DMBJ RVT1C100M0405, 10uF, 16V, ±20%, but the listed package is D4xL5.4mm, not the inventory's 5x5.8 footprint; LCSC showed 2,640 in stock. JLC also lists 10uF 16V parts in D4x5.4mm. Do not treat these as drop-in matches or change CAD. |
| 1N4148W | `D_SOD-123` | 52 | Unassigned. Exact ST(Semtech) 1N4148W, LCSC [C81598](https://www.lcsc.com/product-detail/C81598.html), SOD-123, 75V switching diode. LCSC showed 3,987,150 in stock. Earlier JLC exact-part snapshot: 5,154,966 in stock / 4,829,605 available to order; manufacturer field reads ST(Semtech), not STMicroelectronics. Exact package/value match; assign only through the normal BOM review. |
| 74AHCT595S16-13 | `SOIC-16_3.9x9.9mm_P1.27mm` | 8 | Approved assignment: Diodes Incorporated 74AHCT595S16-13, LCSC/JLC [C126402](https://www.lcsc.com/product-detail/C126402.html) / [JLC listing](https://jlcpcb.com/partdetail/DiodesIncorporated-74AHCT595S1613/C126402). Exact AHCT family and SO-16 / 1.27mm pitch package match; the manufacturer pinout and package drawing are documented in `two_layer/AHCT_STOCK_REVIEW.md`. Latest sourcing review showed 410 at LCSC and 405 available to order at JLC, with 413 total JLC stock in its catalog snapshot. JLC supports SMT assembly. This is the sole approved mapping; do not substitute HC/HCT or mark DNP. |
| TL074 | `SOIC-14_3.9x8.7mm_P1.27mm` | 15 | Unassigned. TI TL074CDR, LCSC [C12594](https://www.lcsc.com/product-detail/C12594.html) / [JLC listing](https://jlcpcb.com/partdetail/TexasInstruments-TL074CDR/C12594), is SOIC-14. LCSC showed 100,145 in stock. Current JLC search result showed 30,187 available to order; an earlier JLC snapshot showed 95,496 / 94,883, so use the fresher 30,187 result and recheck at quote. Inventory has not mapped it. |
| L7805CV | `TO-220-3_Vertical` | 1 | Mapped to ST L7805CV, LCSC [C111887](https://www.lcsc.com/product-detail/C111887.html). Manual soldering, not a JLC SMT placement. LCSC/JLC snapshots showed 26,182 / 26,016 respectively; JLC listing is Extended wave-soldering, not ordinary SMT placement. Confirm exact suffix/package and required mounting before procurement. |
| MountingHole | `MountingHole_3.2mm_M3_Pad` | 14 | Mechanical PCB features, not purchased electronic components; no vendor code assigned. |
| PinHeader_2x38_Straddle | `PinHeader_2x38_Straddle_P2.54mm` | 6 | Manual/THT straddle edge headers. Generic value alone does not specify mating height, plating, pin length, or row/bar configuration for exact procurement. No exact manufacturer part/stock verified; do not infer a substitute. |
| +15V_GND_-15V | `PinHeader_1x03_P2.54mm_Vertical` | 1 | Manual header. No exact manufacturer part/stock verified. |
| 3V3_GND_FROM_MCU | `PinHeader_1x02_P2.54mm_Vertical` | 1 | Manual header. No exact manufacturer part/stock verified. |
| MCU_3V3_SPI_PIN1_NC | `PinHeader_1x06_P2.54mm_Vertical` | 1 | Manual header. No exact manufacturer part/stock verified. |
| Scores_DIV_3V3_Out | `PinHeader_1x12_P2.54mm_Vertical` | 1 | Manual header. No exact manufacturer part/stock verified. |
| Slot0: DC1A (L1 Neurons 0..3) | `PinSocket_2x38_P2.54mm_Vertical` | 1 | Manual socket. No exact manufacturer part/stock verified; mating height and compatibility with straddle header need confirmation. |
| Slot1: DC1B (L1 Neurons 4..7) | `PinSocket_2x38_P2.54mm_Vertical` | 1 | Manual socket. No exact manufacturer part/stock verified; mating height and compatibility with straddle header need confirmation. |
| Slot2: DC1C (L1 Neurons 8..11) | `PinSocket_2x38_P2.54mm_Vertical` | 1 | Manual socket. No exact manufacturer part/stock verified; mating height and compatibility with straddle header need confirmation. |
| Slot3: DC1D (L1 Neurons 12..15) | `PinSocket_2x38_P2.54mm_Vertical` | 1 | Manual socket. No exact manufacturer part/stock verified; mating height and compatibility with straddle header need confirmation. |
| Slot4: DC2 (16x Active Precision ReLU) | `PinSocket_2x38_P2.54mm_Vertical` | 1 | Manual socket. No exact manufacturer part/stock verified; mating height and compatibility with straddle header need confirmation. |
| Slot5: DC3 (L2 Weights + 10-Way WTA) | `PinSocket_2x38_P2.54mm_Vertical` | 1 | Manual socket. No exact manufacturer part/stock verified; mating height and compatibility with straddle header need confirmation. |

## 0.33uF note

There is no 0.33uF inventory group in the current 1,249-item JSON. The previously investigated YAGEO C107132 330nF, 50V, 0805 part had typical simulated DC-bias loss around 20–25% at 15.75V and did not establish a guaranteed effective capacitance of at least 330nF. It is therefore not a verified alternate for a guaranteed 330nF-at-bias requirement, and is not assigned here. The approved bypass-selection instruction was to prefer a 1uF 50V 0805 option without a guaranteed-capacitance release gate; C28323's present stock data is conflicted above, so recheck orderability. No CAD change is implied.

## PCBWay and assembly coverage

No per-part PCBWay catalog confirmation, seven-board BOM upload, PCBA quote, or order was made as part of this review. Exact PCBWay component availability, package acceptance, quantity, assembly fee, shipping, and taxes/duties to Vancouver remain unverified. A JLC listing or LCSC stock count is not evidence of PCBWay stock. For the connectors and L7805CV, preserve the inventory's manual solder classification; do not count them as SMD assembly placements. Any PCBWay board-only or board-plus-SMD-only cost comparison still requires the final seven-board BOM and fabrication data.

## Sources and qualification notes

Exact product links are embedded in the table. Additional first-party package evidence for the approved shift register is collected in [`AHCT_STOCK_REVIEW.md`](AHCT_STOCK_REVIEW.md). Stock counts above are captured catalog snapshots dated 2026-10-04; they are not reservations and must be refreshed in the actual supplier BOM/quote flow. Where a current count is absent or search results conflict, the status is explicitly left unverified rather than called unavailable.