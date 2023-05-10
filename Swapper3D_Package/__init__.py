# /*
# * View model for Swapper3D
# *
# * Author: BigBrain3D
# * License: AGPLv3
# */
 
import octoprint.plugin
import serial

class Swapper3DPlugin(octoprint.plugin.StartupPlugin,
                      octoprint.plugin.TemplatePlugin,
                      octoprint.plugin.SettingsPlugin,
                      octoprint.plugin.EventHandlerPlugin):
    def __init__(self):
        self._swapper3d_connection = None

    def on_after_startup(self):
        # Connect to the Swapper3D here, using the settings
        pass

    def get_settings_defaults(self):
        return {"swap_location": (0, 0)}

    def get_template_configs(self):
        return [
            {"type": "settings", "custom_bindings": True},
            {"type": "tab", "name": "Swapper3D", "custom_bindings": True},
        ]

    def on_event(self, event, payload):
        if event == "PrintPaused":
            # Handle the tool change here
            pass

    def get_update_information(self):
        return dict(
            swapper3d=dict(
                displayName="Swapper3D Plugin",
                displayVersion=self._plugin_version,
                type="github_release",
                user="BigBrain3D",
                repo="Swapper3D_Octoprint_Plugin_V1",
                current=self._plugin_version,
                pip="https://github.com/BigBrain3D/Swapper3D_Octoprint_Plugin_V1/archive/{target_version}.zip"
            )
        )

__plugin_name__ = "Swapper3D Plugin"
__plugin_pythoncompat__ = ">=2.7,<4"
__plugin_implementation__ = Swapper3DPlugin()
