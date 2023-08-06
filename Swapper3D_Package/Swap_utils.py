# Octoprint plugin name: Swapper3D, File: Swap_utils.py, Author: BigBrain3D, License: AGPLv3

from .Swapper3D_utils import perform_command, send_plugin_message

# Function to position for swap
#!!!this is wrong. it's like part bore alignment and part Swap prep. 
#What is the M118 for anyway? explain!
#   M118 if sent to the printer, the printer will wait for all movements to finish because of the G4 
#   and then the M118 will simply echo back the line in quotes 
#   octoprint will then monitor the incoming statements and look for 
def position_for_bore_alignment(plugin):
    # Get the min_z_height from the settings
    min_z_height = plugin._settings.get(["zHeight"])
    x_pos = plugin._settings.get(["xPos"])
    y_pos = plugin._settings.get(["yPos"])

    # Create the list of GCODE commands
    gcode_commands = [
        "M84 X S999",  # Keep the X-axis stepper motors enabled indefinitely
        "G28 XYZ", #home all axis just for bore alignment, swap doesn't need this since the printer is homed at the start of each print.
        f"G1 X{str(x_pos)} Y0 Z{str(min_z_height)}",  # Raise Z to the min Z height
        "G4", # the G4 command will wait until the previous movement commands are complete before it allows any more commands to be queued
        'M118 E1 "readyforborealignment"', # Echo command
    ]

    send_plugin_message(plugin, f"Sending commands to printer to position extruder for Bore Alignment")
            

    # Send the G-code commands to position for swap
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