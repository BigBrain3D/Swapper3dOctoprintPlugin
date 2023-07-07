# Octoprint plugin name: Swapper3D, File: Swap_utils.py, Author: BigBrain3D, License: AGPLv3

from .Swapper3D_utils import perform_command, send_plugin_message

# Function to position for swap
def positioned_for_bore_alignment(plugin):
    # Get the min_z_height from the settings
    min_z_height = plugin._settings.get(["zHeight"])

    # Create the list of GCODE commands
    gcode_commands = [
        f"G1 Z{str(min_z_height)}",  # Raise Z to the min Z height
        "M84 X",  # Keep the X-axis stepper motors enabled indefinitely
        'M117 E1 "ReadyForBoreAlignment"', # Echo command
    ]

    send_plugin_message(plugin, f"Sending commands to printer to position extruder for Swap")
            

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
