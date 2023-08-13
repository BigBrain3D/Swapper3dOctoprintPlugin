# Octoprint plugin name: Swapper3D, File: Swap_utils.py, Author: BigBrain3D, License: AGPLv3

from .Swapper3D_utils import perform_command, send_plugin_message


# def SendStartGcodeToPrinter(plugin):
    #fill this in with the initial gcode required
    #set the Z stepper current

# Function to prepare the Printer for a swap
#   M118 if sent to the printer, the printer will wait for all movements to finish because of the G4 
#   and then the M118 will simply echo back the line in quotes 
#   octoprint will then monitor the incoming statements and look for 
def PreparePrinterForSwap(plugin, currentZofPrinter, HomeAxis):
    # Get the min_z_height from the settings
    min_z_height = plugin._settings.get(["zHeight"])
    x_pos = plugin._settings.get(["xPos"])
    y_pos = plugin._settings.get(["yPos"])
    
    # Initialize the gcode_commands list. Add "G28 XYZ" if HomeAxis is True.
    gcode_commands = ["M84 X S999"]  # Keep the X-axis stepper motors enabled indefinitely
    if HomeAxis:
        gcode_commands.append("G28 XYZ") # Home all axis if HomeAxis is set to True
   
    # Move to the specific X and Y coordinates
    gcode_commands.append(f"G1 X{x_pos} Y{y_pos}")  

    # Check if the Z movement is necessary
    if currentZofPrinter < min_z_height:
        gcode_commands.append(f"G1 Z{str(min_z_height)}")  # Raise Z to the min Z height if needed
        
    # Add the remaining commands
    gcode_commands.extend([
        "G4",  # The G4 command will wait until the previous movement commands are complete before it allows any more commands to be queued
        'M118 E1 "readyforborealignment"'  # Echo command
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
    send_plugin_message(plugin, f"Sending command to turn off bore alignment")
    return perform_command(plugin, command)