# Octoprint plugin name: Swapper3D, File: __init__.py, Author: BigBrain3D, License: AGPLv3

import octoprint.plugin
import serial  # import pySerial for serial communication
import threading  # for running the serial communication in a separate thread
from .commands import handle_command  # import the handle_command function

class Swapper3DPlugin(octoprint.plugin.StartupPlugin,
                      octoprint.plugin.TemplatePlugin,
                      octoprint.plugin.AssetPlugin,
                      octoprint.plugin.BlueprintPlugin,
                      octoprint.plugin.SettingsPlugin,
                      octoprint.plugin.EventHandlerPlugin):  # added EventHandlerPlugin

    def __init__(self):
        self.serial_conn = None  # to hold our serial connection
        self.serial_thread = None  # to hold our thread

    def on_after_startup(self):
        self._logger.info("Swapper3D has started!")

    def get_settings_defaults(self):
        return dict(xPos="0", yPos="0", zHeight="0", gcode="")

    def get_template_configs(self):
        return [
            {"type": "settings", "custom_bindings": False}
        ]

    def get_assets(self):
        return {"js": ["js/Swapper3D_ViewModel.js"]}

    @octoprint.plugin.BlueprintPlugin.route("/command", methods=["POST"])
    def handle_blueprint_command(self):
        return handle_command(self)  # use the imported function

    def serial_loop(self):
        while True:
            if self.serial_conn is None:
                break

            if self.serial_conn.in_waiting:
                line = self.serial_conn.readline().decode()
                self._logger.info("Received from Arduino: " + line)

    def get_update_information(self):
        return dict(
            Swapper3D=dict(
                displayName="Swapper3D",
                displayVersion=self._plugin_version,
                type="github_release",
                user="BigBrain3D",
                repo="Swapper3D_Octoprint_Plugin_V1",
                current=self._plugin_version,
                pip="https://github.com/BigBrain3D/Swapper3D_Octoprint_Plugin_V1/archive/refs/tags/{target_version}.zip",
                events=dict(  # register the custom event
                    Swapper3DLog=True,
                )
            )
        )

    def is_blueprint_csrf_protected(self):
        return True


__plugin_version__ = "0.1.0"
__plugin_description__ = "A plugin controlling the Swapper3D"
__plugin_author__ = "BigBrain3D"
__plugin_url__ = "https://github.com/BigBrain3D/Swapper3D"
__plugin_license__ = "AGPLv3"
__plugin_pythoncompat__ = ">=3.10,<4"  # Compatible python versions
__plugin_implementation__ = Swapper3DPlugin()
