# Current Lucas assembly directive

The restored pre-Economic motherboard geometry remains the approved target. Chips and their bypass capacitors are top; PWM/bulk/rail/reg parts retain the old bottom placement. Keep every reference adjacent to its own component and fix bottom PWM overlap. Route to strict zero errors and zero unconnected, then render populated top and bottom. Daughters remain unchanged.

Latest clarification supersedes the earlier bare-board-only and inactive-exporter notes. This is JLC Economic hybrid assembly. The motherboard assembly side is Bottom. Keep export_sourcing_inventory.py ACTIVE and classify using actual board pad side after restoration. economic_smd_bom contains bottom SMD only. manual_bom contains every top SMD and every THT part; mechanical holes stay mechanical.

All eight approved Diodes 74AHCT595S16-13 C126402 registers will be on top and are MANUAL, purchased and soldered by Lucas. Retain approved exact part sourcing but exclude these references from the JLC assembly BOM and CPL. Top C_SR, R_REF/R_ADC/R_TOP/R_BOT and D_HI/D_LO are also manual. Do not use obsolete Economic placement inventories as evidence of the restored side counts.

Preserve committed Economic versions/backups and all daughter/root originals. Regenerate inventories only against the actual restored authoritative board after coordinated routing ownership handoff. No fabrication release or order.
