# Octoprint plugin name: Swapper3D, File: default_settings.py, Author: BigBrain3D, License: AGPLv3
def get_default_settings():
    return dict(
        xPos = "250",
        yPos = "0.5",
        yBreakStringPosition = "175",
        yBreakStringSpeed = "10200",
        xPositionAfterWipe = "100",
        BreakString = 1,
        xMinPositionForWipe="215",
        xMaxPositionForWipe="230",
        DelayAfterExtruderMovedToWipeLocationBeforeDeployingWiper="200",
        MinExtrusionBeforeSwap="10",
        zHeight = "95",
        ExtraExtrusionAfterSwap = "0.0",
        StockExtruderMaxFeedrate = "120.0",
        SwapExtruderMaxFeedrate = "500.0",
        StockExtruderMaxAcceleration = "5000",
        SwapExtruderMaxAcceleration = "15000",
        zMotorCurrent = "900",
        extrudeSpeedPulldown = "12000",
        retractSpeed= "10000",
        extrudeLengthLockingHeight="18.2",
        extrudeLengthCuttingHeight="39.8",
        retractLengthAfterCut="-70.0",
        msDelayAfterExtrude = "115",
        msDelayPerDegreeMovedDuringSwapPulldown = "6",
        NozzleWipe=1,
        extrudeSpeedPaletteCuts = "12000",
        numPaletteCuts = "3",
        lengthAdditionalCut = "15",
        delayAfterCut = "100",
        motorType = "Standard",
        totalNumberSwaps = "0",
        actuations = "0",
        TR = "0",
        TH = "0",
        TL = "0",
        QL = "0",
        HR = "0",
        CR = "0",
        CA = "0",
        WA = "0",
        beforeStartGcode = "M906 [zMotorCurrent]",
        initialToolLoadGcode = """
    ;***************Begin SWAPPER3D gcode**********************
    G1 [zHeight] F1200 ;mmu 82mm, palette 95mm
    G1 [xPos] Y[yPos] F6000;move to swapper location.
    G4 S0 ;clear movement buffer
    ;T[initial_tool]  ;this is the tool we're going to SWAP to
    Swap[initial_tool] ;SWAP
    ; select extruder
    T[initial_tool]
    ; initial load
    ;G1 Z{layer_height+2} F1200
    ;M18 E; disable E so that filament can be pushed in by hand
    G1 X{random(215.0,230.0)} F6000;
    M109 S220
    G92 E0; reset the extruder position
    G1 E20 F800; Move filament to the top of the heatbreak
    ;***************End SWAPPER3D gcode********************** 
    """,
        toolChangeGcode = """
    {if current_extruder != next_extruder}
    ;***************Begin SWAPPER3D gcode**********************
    G1 Y175 F10200 ;Break string before Z lift
    ;check for clearance for the swapper. If none, then lift Z to accomodate
    ;{if layer_z < 82};mmu 82mm, palette 95mm
    G1 Z[zHeight] F1200 ;mmu 82mm, palette 95mm
    ;{endif}
    M107; turn off the layer cooling fan to avoid cooling the heaterblock during swap
    G1 X[xPos] Y[yPos] F6000;move to swapper location.
    G4 S0 ;clear movement buffer
    G92 E0; reset the extruder position
    ;T{next_extruder}  ;this is the tool we're going to SWAP to ;maybe this can be commented out but left here so that the tool command is not inserted, could be a useful strategy ; this must take place before the M921 for reasons in the firmware code
    M921 S{next_extruder} ; was 'current_extruder' ;SWAP
    ;move to the wiper
    ;check for cutter arm clearance. If the print is above the cutter arm clearance then move to wiper min clearance
    ;otherwise move to cutter arm min clearance
    ;Random X position over wiper. Be wiper min above the print.
    ;Current Layer: {layer_z}
    ;{if layer_z >= 32 && layer_z - 32 >= 24}
    ;here1
    G1 X{random(215.0,230.0)} Y125 Z{layer_z+24} F6000;move the relative position the print will restart from during the time the nozzle is heating. This will reduce the time to resume printing by many seconds
    ;{elsif 32 - layer_z < 24}
    ;here2
    G1 X{random(215.0,230.0)} Y125 Z{32+(24-(32-layer_z))} F6000;move the relative position the print will restart from during the time the nozzle is heating. This will reduce the time to resume printing by many seconds
    {else}
    ;here3
    G1 X{random(215.0,230.0)} Y125 Z32 F6000;move the relative position the print will restart from during the time the nozzle is heating. This will reduce the time to resume printing by many seconds
    ;{endif}
    G4;move to location before deploying the wiper
    Wipe ;extend wiper
    G92 E0; reset the extruder position
    G1 E-45 F1200; unload from the extruder
    G92 E0; reset the extruder position
    ;G4 S10; pause ;this may not be needed IF the MMU next filament load is performed first because that takes 10+sec
    M702 C; unload 1st before tool change, otherwise it takes too long and the printer will reset.
    T{next_extruder}  ;trigger the MMU filament switch
    M109 S215 ;Wait for heat to stabilize
    M106 S127; turn the cooling fan back on after the swap
    G1 X175 F10200;move nozzle off left side of wiper
    G4;wait for the x to move
    WipeStow ;stow the wiper 
    ;***************End SWAPPER3D gcode**********************
    {endif}
    """,
        beforeEndGcode = """
    ;***************Begin SWAPPER3D gcode**********************
    G1 Z[zHeight] F1200 ;mmu 82mm, palette 95mm
    G1 X[xPos] Y[yPos] F6000;move to swapper location.
    G4 S0 ;clear movement buffer
    SwapUnload ;SWAP unload hotend
    M702 C ; Unload filament with MMU
    ;***************End SWAPPER3D gcode**********************
    """,
        FilamentSwitcherType = "parallel",
        extraFilamentCutLength = "60",
        lengthEachCut = "15",
    )
