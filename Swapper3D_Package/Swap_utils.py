# Octoprint plugin name: Swapper3D, File: Swap_utils.py, Author: BigBrain3D, License: AGPLv3 

import random
import time
from .Swapper3D_utils import perform_command, send_plugin_message, load_insert, unload_insert, Deploy_Wiper, Stow_Wiper

# def SendStartGcodeToPrinter(plugin):
    #fill this in with the initial gcode required
    #set the Z stepper current

# Function to prepare the Printer for a swap
#   M118 if sent to the printer, the printer will wait for all movements to finish because of the G4 
#   and then the M118 will simply echo back the line in quotes 
#   octoprint will then monitor the incoming statements and look for 
# the reason that we need to do it this way is there is no command to ask the printer if all it's movements are complete
# that means that we would send the command to the printer to move to the XYZ swap position but we could never know when it's finished moving to that position
# instead we issue a command to move followed by a G4 followed by the M118 command to echo. 
# this is what happens: 
# 1) the printer queues all the commands
# 2) the printer tries to execute all the commands at the same time
# 3) but it runs into a G4 which tells it to finish all the movement commands before executing any new commands
# 4) the printer finishes all the movement commands which satisfies the G4 command
# 5) the printer executes the M118 echo command
# 6) Octoprint , which has been monitoring all outgoing printer communications, receives the echo "some octoprint command (ready for swap, or ready for bore alignment, for example)
# 7) octoprint now knows that the print head is in the swap position
# 8) octoprint executes the requested command
def PreparePrinterForSwap(plugin, currentZofPrinter, HomeAxis, EchoCommand):
    # Get the min_z_height from the settings
    min_z_height = plugin._settings.get(["zHeight"])
    x_pos = plugin._settings.get(["xPos"])
    y_pos = plugin._settings.get(["yPos"])
    yBreakStringPosition = plugin._settings.get(["yBreakStringPosition"])
    yBreakStringSpeed = plugin._settings.get(["yBreakStringSpeed"])
    BreakString = plugin._settings.get(["BreakString"])
    
    
    
    # Initialize the gcode_commands list. Add "G28 XYZ" if HomeAxis is True.
    gcode_commands = ["M84 X S999", # Keep the X-axis stepper motors enabled indefinitely
                      "M107"] # Turn off cooling fan
    
    if BreakString:
        gcode_commands.append(f"G1 Y{yBreakStringPosition} F{yBreakStringSpeed}") #Y move to break the string before Z lift)
    
    gcode_commands.append("G4")
    
    if HomeAxis:
        gcode_commands.append("M211 S0")  # Added on Aug 16th 2024.
        gcode_commands.append("G411 S0")  # Added on Aug 16th 2024.
        gcode_commands.append("G1 X-10 F2000")  # Added on Aug 16th 2024. When a homing command is issued the printer automatically moves to the right some mm, which causes it to crash into the swapper and stop homing X, which then causes the head to be too far to the right for the Z home which causes the head to crash into the bed because the PINDA probe is off the right side of the bed. Adding a small movement to the left should prevent this.
        gcode_commands.append("M211 S1")  # Added on Aug 16th 2024.
        gcode_commands.append("G4")  # Added on Aug 16th 2024.
        gcode_commands.append("G28 XYZ")  # Home all axis if HomeAxis is set to True
   
    # Send message with currentZofPrinter and min_z_height values
    send_plugin_message(plugin, f"Swapper3D_utils.PreparePrinterForSwap.currentZofPrinter: {currentZofPrinter}, min_z_height: {min_z_height}")
    
    # Check if the Z movement is necessary
    if int(currentZofPrinter) < int(min_z_height):
        gcode_commands.append(f"G1 Z{min_z_height}")  # Move Z only the needed amount
        
    # Move to the specific X and Y coordinates
    gcode_commands.append(f"G1 X{x_pos} Y{y_pos} F6000")

        
    # Add the remaining commands
    gcode_commands.extend([
        "G4",  # The G4 command will wait until the previous movement commands are complete before it allows any more commands to be queued
        f"M118 E1 {EchoCommand}",   # Echo command updated
        f"M117 E1 {EchoCommand}"   # Echo command updated works with virtual printer
    ])

    send_plugin_message(plugin, f"Sending commands to printer to Prepare Printer For Swap")

    # Send the G-code commands to prepare for swap
    plugin._printer.commands(gcode_commands)
        

# Function to turn on bore alignment
def bore_align_on(plugin):
    command = "borealignon"
    send_plugin_message(plugin, f"Sending command to turn on bore alignment")
    return perform_command(plugin, command)

# Function to turn off bore alignment
def bore_align_off(plugin):
    command = "borealignoff"
    plugin._printer.commands("@resume")
    send_plugin_message(plugin, f"Sending command to turn off bore alignment")
    return perform_command(plugin, command)
    
    
def swap(plugin):
    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Swap_utils.swap: In Swap!"))
    NozzleWipe = plugin._settings.get(["NozzleWipe"])
    xMinPositionForWipe = int(plugin._settings.get(["xMinPositionForWipe"]))
    xMaxPositionForWipe = int(plugin._settings.get(["xMaxPositionForWipe"]))
    randomXpositionForWipe = random.randint(xMinPositionForWipe,xMaxPositionForWipe)
    DelayAfterExtruderMovedToWipeLocationBeforeDeployingWiper = int(plugin._settings.get(["DelayAfterExtruderMovedToWipeLocationBeforeDeployingWiper"]))
    xPositionAfterWipe = int(plugin._settings.get(["xPositionAfterWipe"]))
    yBreakStringSpeed = plugin._settings.get(["yBreakStringSpeed"])
    ExtraExtrusionAfterSwap = plugin._settings.get(["ExtraExtrusionAfterSwap"])
    RetractionDistanceAfterSwap = plugin._settings.get(["RetractionDistanceAfterSwap"])
    
    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"randomXpositionForWipe:{randomXpositionForWipe}"))

    #if the current_extruder is not None then unload first
    if plugin.insertLoaded:
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="There is a currently loaded insert. Attempting to unload Insert."))

        unload_result = unload_insert(plugin)


    #Load the next insert
    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Swap_utils.swap.next_extruder:{plugin.next_extruder}"))
    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"1.Aug23.Swap_utils.swap.next_extruder:Aug 23->about to initiate load"))
    load_insert(plugin, plugin.next_extruder)
    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"4.Aug23.Swap_utils.swap.next_extruder:Past initiate load"))
                          
    #if the wipe procedure is ON
    #move extruder to RANDOM X-axis wipe location
    #deploy the wiper to RANDOM angle
    if NozzleWipe:
        gcode_commands = [f"G1 X{randomXpositionForWipe} F6000",
                           "G4"]
        plugin._printer.commands(gcode_commands)
        
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Swap_utils.swap:Waiting for random X move"))
        time.sleep(DelayAfterExtruderMovedToWipeLocationBeforeDeployingWiper/1000) #Delay after moving extruder to wipe location
        
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Swap_utils.swap:Waiting to deloy wiper"))
        #deploy the wiper
        Deploy_Wiper(plugin)
        
    #change tool
    #send WAIT for temp heat up
    #signal temp heat up complete with M117/M118
    gcode_commands =[f"T{plugin.next_extruder}",
                     f"M109 S{plugin.currentTargetTemp}", #Wait for heat to stabilize
                     "G4",
                     "G92 E0; reset the extruder position",
                     "G4",
                     f"G1 E{ExtraExtrusionAfterSwap} F300",
                     "G4",
                     "G92 E0; reset the extruder position",
                     "G4",
                     f"G1 E-{RetractionDistanceAfterSwap} F2100",
                     "G92 E0; reset the extruder position",
                     "G4",
                     f"G1 X{xPositionAfterWipe} F{yBreakStringSpeed}", #move extruder off the wipe pad (this is the actual "wipe")
                     "G4",
                     "M118 E1 StowWiper",   # Echo command updated works with i3
                     "M117 E1 StowWiper"]  # Echo command updated works with virtual printer
    #insert the tool command here so that the filament is switched
    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="Tool change sent by Swap_utils.swap()"))
    plugin._printer.commands(gcode_commands)
    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Aug23.Swap_utils.swap.next_extruder:Printer moves executed. Must be after OK."))

    
    #set the LCD display to show the currently loaded insert
    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Swap_utils.Swap: Setting LCD message: InsertNumber{int(plugin.next_extruder) + 1}"))
    command = f"InsertNumber{int(plugin.next_extruder) + 1}"
    perform_command(plugin, command)
    

    plugin.current_extruder = plugin.next_extruder  # current_extruder becomes next_extruder
    plugin.next_extruder = None

    #because the number of the insert can be none 
    #we need to keep track if the current insert is the first loaded 
    #with an additional flag.
    #once true, even if the currently loaded insert number is none
    #we know that there is actually an insert in there
    #conversely, if the initial load complete var is false then there is
    #nothing to unload
    if not plugin.InitialLoadComplete:
        plugin.InitialLoadComplete = True
        
    
        
    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="*****Swap_utils.swap().Swap complete*****"))
 
        
    return True, str("")