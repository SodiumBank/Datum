# Datum — Rules Catalog (v1)

## Rule Contract
- Deterministic
- Explainable
- Traceable to a ruleset version
- Does not retroactively alter locked revisions

## Rule Categories
- DRC
- DFM
- PROCESS
- TEST
- SUPPLY

## Examples
### PROCESS — NASA polymerics sequencing
- Trigger: polymeric material present OR coating/staking required OR NASA mode
- Action: add steps CLEAN → BAKE → POLYMER → CURE → INSPECT
- Lock sequence: true
- Justification: NASA-STD-8739.1 polymerics requirements; clean before staking/coating; bake after clean; inspect after cure

### TEST — X-ray for hidden joints
- Trigger: package in (BGA, QFN)
- Action: add test XRAY
- Severity: MEDIUM
- Justification: hidden solder joints require inspection

### SUPPLY — long-lead & EEE handling
- Trigger: part lead_time_weeks >= 26 OR is_eee
- Action: add cost INVENTORY_CARRY + EEE_HANDLING; require full cert traceability; optionally declare A/B lot testing
