# /*
# * View model for Swapper3D
# *
# * Author: BigBrain3D
# * License: AGPLv3
# */
 import requests
import octoprint.plugin
import serial

class Swapper3DPlugin(octoprint.plugin.StartupPlugin,
                      octoprint.plugin.TemplatePlugin,
                      octoprint.plugin.SettingsPlugin,
                      octoprint.plugin.EventHandlerPlugin):
    def __init__(self):
        self._swapper3d_connection = None
        self._plugin_version = "0.1.7"  # replace with your current version


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
        data = requests.get("https://api.github.com/repos/BigBrain3D/Swapper3D_Octoprint_Plugin_V1/releases/latest").json()
        return {
            "swapper3d": {
                "displayName": "Swapper3D Plugin",
                "displayVersion": self._plugin_version,
                "type": "github_release",
                "user": "BigBrain3D",
                "repo": "Swapper3D_Octoprint_Plugin_V1",
                "current": self._plugin_version,
                "pip": "https://github.com/BigBrain3D/Swapper3D_Octoprint_Plugin_V1/archive/{target_version}.zip",
                "latest": data["tag_name"]
            }
        }

    def _check_for_plugin_updates(self):
        update_info = self.get_update_information()["swapper3d"]
        if update_info is not None:
            update_type = update_info["type"]
            if update_type == "github_release":
                user = update_info["user"]
                repo = update_info["repo"]
                current_version = update_info["current"]
                latest_version = None
                try:
                    latest_version = self._get_latest_github_release(user, repo)
                except:
                    self._logger.exception("Error checking for plugin updates")

                if latest_version is not None and latest_version != current_version:
                    self._logger.info(f"New version {latest_version} of Swapper3D Plugin is available")
                    self._plugin_manager.notify_user(
                        f"A new version {latest_version} of Swapper3D Plugin is available for update",
                        type="info",
                        timeout=None,
                        done=None
                    )

    def _get_latest_github_release(self, user, repo):
        data = requests.get(f"https://api.github.com/repos/{user}/{repo}/releases/latest").json()
        return data["tag_name"]

__plugin_name__ = "Swapper3D Plugin"
__plugin_pythoncompat__ = ">=2.7,<4"
__plugin_implementation__ = Swapper3DPlugin()

__plugin_hooks__ = {
    "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
    "octoprint.plugin.softwareupdate.check_update_available": __plugin_implementation__._check_for_plugin_updates
}
