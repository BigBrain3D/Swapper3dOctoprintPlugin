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

    def on_event(self, event, payload):
        if event == "PrintStarted":
            # Create a new log file for each print.
            self.log_file_path = os.path.join(os.path.dirname(__file__), 'gcode', f'gcode_{int(time.time())}.txt')
            os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
            self._logger.info("Created a new log file at start of print: " + self.log_file_path)
            
    def on_after_startup(self):
        self._logger.info("Swapper3D has started!")

    def hook_gcode_queuing(self, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None, *args, **kwargs):
        if not self._printer.is_operational() or not self._printer.is_printing():
            return

        if gcode:
            injected_gcode, self.initial_tool_load, self.tool_change_occurred = inject_gcode(
                cmd, self._settings, self.initial_tool_load, self.tool_change_occurred, self._logger, self.log_file_path
            )

            # return the modified gcode
            return [(line, cmd_type, gcode, subcode, tags) for line in injected_gcode]
    
    def on_gcode_received(self, comm, line, *args, **kwargs):
        # Check if the line contains our echo (case insensitive)
        if "readyforborealignment" in line.lower():
            # Finally, turn on bore alignment
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="command echo from printer: borealignon"))
            try:
                success, error = bore_align_on(self)
                if not success:
                    self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Bore alignment on failed: {error}"))
                    return line
            except Exception as e:
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Exception during bore alignment on: {str(e)}"))
                return line

            #self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Bore alignment on successful"))
            #self._plugin_manager.send_plugin_message(self._identifier, dict(type="connectionState", message="Ready to Swap!"))
            
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


    #def serial_loop(self):
    #    while True:
    #        if self.serial_conn is None:
    #            break
    #
    #        if self.serial_conn.in_waiting:
    #            line = self.serial_conn.readline().decode()
    #            self._logger.info("Received from Arduino: " + line)

    def get_update_information(self):
        return dict(
            Swapper3D=dict(
                displayName="Swapper3D",
                displayVersion=self._plugin_version,
                type="github_release",
                user="BigBrain3D",
                repo="Swapper3D_Octoprint_Plugin_V1",
                current=self._plugin_version,
                pip="https://github.com/BigBrain3D/Swapper3D_Octoprint_Plugin/archive/{target_version}.zip"
            )
        )

__plugin_name__ = "Swapper3D"
__plugin_version__ = "0.1.0"
__plugin_description__ = "A plugin controlling the Swapper3D"
__plugin_author__ = "BigBrain3D"
__plugin_url__ = "https://github.com/BigBrain3D/Swapper3D"
__plugin_license__ = "AGPLv3"
__plugin_pythoncompat__ = ">=3.7,<4"  # Compatible python versions
__plugin_implementation__ = Swapper3DPlugin()

def __plugin_load__():
    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.comm.protocol.gcode.received": __plugin_implementation__.on_gcode_received,
        "octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.hook_gcode_queuing
    }
    
    