# Octoprint plugin name: Swapper3D, File: Swap_utils.py, Author: BigBrain3D, License: AGPLv3

from .Swapper3D_utils import perform_command, send_plugin_message

# Function to turn on bore alignment
def bore_align_on(plugin):
    # Get the min_z_height from the settings
    min_z_height = plugin._settings.get(["zHeight"])

    # Now we'll create the list of GCODE commands
    gcode_commands = [
        f"G1 Z{str(min_z_height)}",  # Raise Z to the min Z height
        "M84 X",  # Keep the X-axis stepper motors enabled indefinitely
    ]

    # Send the G-code commands to prepare for bore alignment
    plugin._printer.commands(gcode_commands)

    # Finally, turn on bore alignment
    command = "borealignon"
    send_plugin_message(plugin, f"Sending command to turn on bore alignment")
    return perform_command(plugin, command)



# Function to turn off bore alignment
def bore_align_off(plugin):
    command = "borealignoff"
    send_plugin_message(plugin, f"Sending command to turn off bore alignment")
    return perform_command(plugin, command)
