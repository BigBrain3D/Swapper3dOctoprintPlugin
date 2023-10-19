# Octoprint plugin name: Swapper3D, File: Swap_utils.py, Author: BigBrain3D, License: AGPLv3 

from .Swapper3D_utils import perform_command, send_plugin_message


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
    
    # Initialize the gcode_commands list. Add "G28 XYZ" if HomeAxis is True.
    gcode_commands = ["M84 X S999"]  # Keep the X-axis stepper motors enabled indefinitely
    if HomeAxis:
        gcode_commands.append("G28 XYZ")  # Home all axis if HomeAxis is set to True
   
    # Move to the specific X and Y coordinates
    gcode_commands.append(f"G1 X{x_pos} Y{y_pos}")  


    # Send message with currentZofPrinter and min_z_height values
    send_plugin_message(plugin, f"currentZofPrinter: {currentZofPrinter}, min_z_height: {min_z_height}")
    
    # Check if the Z movement is necessary
    if int(currentZofPrinter) < int(min_z_height):
        gcode_commands.append(f"G1 Z{str(min_z_height)}")  # Raise Z to the min Z height if needed
        
    # Add the remaining commands
    gcode_commands.extend([
        "G4",  # The G4 command will wait until the previous movement commands are complete before it allows any more commands to be queued
        f'M118 E1 "{EchoCommand}"'   # Echo command updated
    ])

    send_plugin_message(plugin, f"Sending commands to printer to Prepare Printer For Swap")

    # Send the G-code commands to prepare for swap
    plugin._printer.commands(gcode_commands)
    
    #pause all gcode commands
    #resumes in the on_gcode_received method init py or the borealignoff
    plugin._printer.commands("@pause")
    

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
    #if the current_extruder is not None then unload first
    if plugin.current_extruder != None:
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="There is a currently loaded insert. Attempting to unload Insert."))
        
        #if there is an insert loaded already then unload it first
        if self.insertLoaded:
            try:
                unload_result = unload_insert(plugin)
                if unload_result != "OK":
                    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Unload failed: {unload_result}"))
                    return jsonify(result="False", error=unload_result), 500
            except Exception as e:
                plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Exception during unload: {str(e)}"))
                return jsonify(result="False", error=str(e)), 500

            plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="Unload successful"))
            return jsonify(result="True")

    #load the next insert
    try:
        success, error = load_insert(plugin, plugin.next_extruder)
        if not success:
            plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Failed to load insert: {error}"))
            return jsonify(result="False", error=str(error)), 500
    except Exception as e:
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Failed to load insert: {str(e)}"))