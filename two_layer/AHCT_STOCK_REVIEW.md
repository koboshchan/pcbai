# AHCT595 sourcing review

Checked 2026-10-04. Research only: no CAD, schematic, BOM, CPL, or assembly files were changed, and nothing was ordered.

## Recommended assembly part

Use Diodes Incorporated **74AHCT595S16-13**, LCSC **C126402**, as the stocked same-package AHCT595 assembly candidate, subject to the normal final BOM/CPL review. It is an AHCT595 eight-bit shift register with latched tri-state outputs, 4.5–5.5 V supply, -40 to +125 °C range, and manufacturer-rated source/sink capability of 8 mA at VCC = 4.5 V. The Diodes manufacturer pin table maps pins 1–16 to Q1, Q2, Q3, Q4, Q5, Q6, Q7, GND, Q7S, MR, SHCP, STCP, OE, DS, Q0, VCC, respectively. This matches the Nexperia 74AHCT595D signal pinout used by the design.

The Diodes part is sold in SO-16 (Type SM). Its manufacturer package drawing specifies 9.80–10.00 mm body length, 3.80–4.00 mm body width, and 1.27 mm lead pitch. The existing `SOIC-16_3.9x9.9mm_P1.27mm` footprint is therefore the correct package geometry; no PCB footprint change is indicated. The Diodes suggested pad layout specifies 1.27 mm lead pitch. LCSC's generic “SOP-16” catalog label is broader than the manufacturer's part-specific SO-16 drawing; the manufacturer drawing, not the generic label, is the basis for this match.

## Current catalog and assembly availability

LCSC currently lists **410 in stock**, with a minimum purchase quantity of 5 and multiples of 5. The visible price is **USD $0.2142 each at 5+**; for eight installed devices, the minimum purchasable quantity is ten, about **USD $2.142** before shipping/tax, with two spares. Higher displayed breaks are $0.1703 at 50+, $0.1514 at 150+, $0.1279 at 500+, $0.1174 at 2,500+, and $0.1111 at 5,000+.

JLCPCB's exact C126402 page lists the part as **Extended**, package SOP-16, with **SMT assembly supported for Economic and Standard PCBA**. It showed **413 in stock** and **405 available to order** when checked. Displayed JLC unit prices are USD $0.2146 at 1+, $0.1706 at 50+, $0.1517 at 150+, $0.1282 at 500+, $0.1177 at 2,500+, and $0.1114 at 5,000+. The page says these components are stored in the JLC parts library for future PCBA orders and cannot be shipped separately. Inventory can change; recheck at quote/order time. These are catalog/parts-library quantities, not a final assembly quote.

## Other examined options

The original Nexperia **74AHCT595D,112**, LCSC **C554704**, is out of stock at LCSC. Nexperia's package code SOT109-1 is the same SO16 3.9 mm-body, 1.27 mm-pitch package. Manufacturer packing documents identify suffix **,112** as tube packing and **,118** as 13-inch reel packing; these suffixes do not change the SO16 package or device pinout.

Nexperia **74AHCT595D,118**, LCSC/JLC C503428, is a genuine same-device alternate package option, but both LCSC and JLC pages showed only **2 in stock**, not enough for the eight installed positions. JLC showed $0.4065 each at 1+; LCSC's displayed lowest tier is not a quote for a quantity of eight. Do not use this listing for this build unless inventory changes.

The Diodes C126402 option is preferable to switching the design to HCT: it retains the AHCT input family and is available in sufficient quantity at both LCSC and JLC. This is sourcing evidence, not an authorization to silently alter CAD. Keep all eight U_SR1–U_SR8 on the existing SOIC-16 footprint. The project owner should update only the purchasing/BOM and assembly CPL mapping to C126402 after approval/review; preserve the full BOM and ensure the assembly list assigns the eight references to this candidate. Do not mark these eight DNP if sourcing this part for assembly. No circuit or routing change is indicated by this package/pinout comparison. Final electrical-model qualification remains separate from catalog equivalence, especially if a model assumes a particular intermediate-load VOH/VOL or output impedance.

## Sources

- LCSC C126402 listing, manufacturer code, 410 stock, quantity multiples, and price breaks: https://www.lcsc.com/product-detail/C126402.html
- JLCPCB C126402 listing, 413 stock / 405 available, SMT assembly support, and price breaks: https://jlcpcb.com/partdetail/DiodesIncorporated-74AHCT595S1613/C126402
- Diodes Incorporated 74AHCT595 datasheet, pin descriptions, ratings, SO-16 outline, and ordering code: https://www.diodes.com/datasheet/download/74AHCT595.pdf
- Diodes Incorporated SO-16 Type SM package outline and suggested land pattern: https://www.diodes.com/assets/Package-Files/SO-16-Type-SM.pdf
- Nexperia 74AHC/74AHCT595 datasheet, SO16/SOT109-1 body dimensions and pinout: https://assets.nexperia.com/documents/data-sheet/74AHC_AHCT595.pdf
- Nexperia SOT109-1 package drawing: https://assets.nexperia.com/documents/package-information/SOT109-1.pdf
- Nexperia ,112 tube packing document: https://assets.nexperia.com/documents/packing-information/SOT109-1_112.pdf
- Nexperia ,118 13-inch reel packing document: https://assets.nexperia.com/documents/packing-information/SOT109-1_118.pdf
- LCSC Nexperia C503428 listing: https://www.lcsc.com/product-detail/C503428.html
- JLCPCB Nexperia C503428 listing: https://jlcpcb.com/partdetail/Nexperia-74AHCT595D118/C503428
- LCSC original C554704 listing: https://www.lcsc.com/product-detail/shift-registers_nexperia-74ahct595d-112_C554704.html
