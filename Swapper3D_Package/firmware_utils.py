# Octoprint plugin name: Swapper3D, File: firmware_utils.py, Author: BigBrain3D, License: AGPLv3
import os
from github import Github
import requests

def download_latest_firmware(self, firmware_type):
    g = Github()  # Create an unauthenticated client

    # Repositories URLs
    repositories = {
        "runtime_firmware": "BigBrain3D/Swapper3D_Firmware",
        "servo_setup": "BigBrain3D/Swapper3D_ServoSetup"
    }

    # Directories to save the firmware files
    directories = {
        "runtime_firmware": os.path.join(self.get_plugin_data_folder(), "runtimeFirmware"),
        "servo_setup": os.path.join(self.get_plugin_data_folder(), "servoSetup")
    }

    # Check if the firmware type is valid
    if firmware_type not in repositories:
        self._plugin_manager.send_plugin_message(
            self._identifier, 
            dict(type="log", message=f"Invalid firmware type: {firmware_type}")
        )
        return False

    # Download the latest firmware file from the selected repo
    repo_url = repositories[firmware_type]
    repo = g.get_repo(repo_url)
    latest_release = repo.get_latest_release()
    directory = directories[firmware_type]

    for asset in latest_release.get_assets():
        download_url = asset.browser_download_url
        file_name = os.path.join(directory, f"{latest_release.tag_name}.hex")
        try:
            download_file(download_url, file_name, self)
            self._plugin_manager.send_plugin_message(
                self._identifier, 
                dict(type="log", message=f"Downloaded file: {file_name}")
            )
            return True
        except Exception as e:
            self._plugin_manager.send_plugin_message(
                self._identifier, 
                dict(type="log", message=f"Failed to download file: {str(e)}")
            )
    return False


# Function to download a file from a url and save it to a file
def download_file(url, filename, self):
    # Check if the file already exists
    if os.path.isfile(filename):
        # If it does, delete it
        os.remove(filename)
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Existing file deleted: {filename}"))
    
    try:
        # Download the file
        response = requests.get(url, stream=True)
    
        if response.status_code == 200:  # Check if the request was successful
            with open(filename, 'wb') as fd:
                for chunk in response.iter_content(chunk_size=128):
                    fd.write(chunk)
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"File downloaded successfully: {filename}"))
        else:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Failed to download file: {filename}"))
            return False
    
    except Exception as e:
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Exception occurred while downloading file: {str(e)}"))
        return False
    
    return True

