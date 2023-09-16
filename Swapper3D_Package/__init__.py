# Octoprint plugin name: Swapper3D, File: __init__.py, Author: BigBrain3D, License: AGPLv3
import os
import time
import octoprint.plugin
import serial
import threading
from .commands import handle_command
from .gcode_injector import inject_gcode
from .default_settings import get_default_settings
from .Swap_utils import bore_align_on, bore_align_off

class Swapper3DPlugin(octoprint.plugin.StartupPlugin,
                      octoprint.plugin.TemplatePlugin,
                      octoprint.plugin.AssetPlugin,
                      octoprint.plugin.BlueprintPlugin,
                      octoprint.plugin.SettingsPlugin,
                      octoprint.plugin.EventHandlerPlugin):  # added EventHandlerPlugin

    def __init__(self):
        super().__init__()
        self.serial_conn = None  # to hold our serial connection
        self.serial_thread = None  # to hold our thread
        self.initial_tool_load = False
        self.tool_change_occurred = False
        self.log_file_path = os.path.join(os.path.dirname(__file__), 'gcode', f'gcode_{int(time.time())}.txt')
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
        self.is_print_started = False #custom flag to track if we already injected the start print commands needed for the swapper
        self.current_extruder = None  # Initialize current_extruder as None
        self.next_extruder = None  # Initialize next_extruder as None

    def on_event(self, event, payload):
        if event == "PrintStarted":
            # Create a new log file for each print.
            self.log_file_path = os.path.join(os.path.dirname(__file__), 'gcode', f'gcode_{int(time.time())}.txt')
            os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
            self._logger.info("Created a new log file at start of print: " + self.log_file_path)
            
    def on_after_startup(self):
        self._logger.info("Swapper3D plugin has started!")

    def hook_gcode_queuing(self, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None, *args, **kwargs):
        #return if the printer is not connected
        #return if there is no print running
        if not self._printer.is_operational() or not self._printer.is_printing():
            return (cmd, cmd_type, gcode, subcode, tags)
        
        #is the Swapper3D is disconnected then don't do any swap prep or swaps
        if self.serial_conn is None:
            return (cmd, cmd_type, gcode, subcode, tags)

        #return if gcode is empty
        if not gcode:
            return (cmd, cmd_type, gcode, subcode, tags)
            
        #return if the gcode is not a Tool change
        # If the command is a 'T' command, we need to update the current_extruder and next_extruder
        if not gcode.startswith("T"):
            return (cmd, cmd_type, gcode, subcode, tags)
        
        self.next_extruder = cmd[1:]  # Capture everything after T as the current extruder (e.g., for T1, current_extruder will be '1')

        # Check if it's the start of the print
        if not self.is_print_started:
            z_motor_current = self._settings.get(["zMotorCurrent"])
            self._printer.commands(f"M906 {z_motor_current}")  # insert the command
            self.is_print_started = True  # Update the flag after the start of the print
            return (cmd, cmd_type, gcode, subcode, tags)


        #return if the next Tool is the same as the current Tool
        #if the current and next T command are the same exit without Swapping
        #also return an empty GCODE so that the filament switcher doesn't waste time removing and adding the exact same filament
        #will this mess with the palette or P2PP because they may have extra length to account for that extra tool change???????
        if self.current_extruder == self.next_extruder:
            return
            
        HomeAxis = False  # Assuming you want to Home Axis when borealignon command is received
        current_z = self._printer.get_current_data()["currentZ"]   # Get the current Z height
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="current_z", message=str(current_z)))
        PreparePrinterForSwap(self, current_z, HomeAxis, "readyforswap")#suspend all gcode queueing until the swap is complete in on_gcode_received
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="currentlyLoadedInsert", message=str(insert_number)))
        return


    def on_gcode_received(self, comm, line, *args, **kwargs):
        # Check if the line contains our echo (case insensitive)
        if "readyforborealignment" in line.lower():
            # Finally, turn on bore alignment
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="command echo from printer: borealignon"))
            try:
                success, error = bore_align_on(self)
                
                self._printer.commands("@resume")

                if not success:
                    self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Bore alignment on failed: {error}"))
                    return line
            except Exception as e:
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Exception during bore alignment on: {str(e)}"))
                return line

        if "readyforswap" in line.lower():
            # Finally, turn on bore alignment
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="command echo from printer: readyforswap"))
            try:
                success, error = swap(self)
                
                #insert the tool command here so that the filament is switched
                gcode_commands = f"T{self.next_extruder}"
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Injecting Tool change: {gcode_commands}"))
                self._printer.commands(gcode_commands)
                
                #what about the wipe?
                
                self.current_extruder = self.next_extruder  # current_extruder becomes next_extruder
                self.next_extruder = None
                self._printer.commands("@resume")

                if not success:
                    self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Swap failed: {error}"))
                    return line
            except Exception as e:
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Exception during Swap: {str(e)}"))
                return line
                
        return line
        
            
    def get_template_configs(self):
        return [
            {"type": "settings", "custom_bindings": False}
        ]

    def get_assets(self):
        return {"js": ["js/Swapper3D_ViewModel.js"]}

    @octoprint.plugin.BlueprintPlugin.route("/command", methods=["POST"])
    def handle_blueprint_command(self):
        return handle_command(self)  # use the imported function

    def is_blueprint_csrf_protected(self):
        return True
        
    def get_settings_defaults(self):
        default_settings = get_default_settings()
        self._logger.debug(f"Default settings: {default_settings}")
        return default_settings

    def get_update_information(self):
        return dict(
            Swapper3D=dict(
                displayName="Swapper3D",
                displayVersion=self._plugin_version,
                type="github_release",
                user="BigBrain3D",
                repo="Swapper3dOctoprintPlugin",
                current=self._plugin_version,
                pip="https://github.com/BigBrain3D/Swapper3D_Octoprint_Plugin/archive/{target_version}.zip",
                pip_args=["--no-cache-dir", "--ignore-installed", "--force-reinstall"]
            )
        )


__plugin_name__ = "Swapper3D"
__plugin_version__ = "0.2.9" 
__plugin_description__ = "An Octoprint plugin for Controlling the Swapper3D"
__plugin_author__ = "BigBrain3D"
__plugin_url__ = "https://github.com/BigBrain3D/Swapper3dOctoprintPlugin"
__plugin_license__ = "AGPLv3"
__plugin_pythoncompat__ = ">=3.7,<4"  # Compatible python versions
__plugin_implementation__ = Swapper3DPlugin()

def __plugin_load__():
    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.comm.protocol.gcode.received": __plugin_implementation__.on_gcode_received,
        "octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.hook_gcode_queuing,
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
    
def get_update_hooks(self):
    return {
        "octoprint.plugin.softwareupdate.check_config": self.get_update_information
    }