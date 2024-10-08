# Octoprint plugin name: Swapper3D, File: commands.py, Author: BigBrain3D, License: AGPLv3

from flask import request, jsonify
from .Swapper3D_utils import * #import all methods
from .Swap_utils import *
import time

def handle_command(self):
    data = request.json
    command = data.get("command")

    if command == "connect":
        if self.serial_conn is not None:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Already connected."))
            return jsonify(result="False"), 500

        self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Received command: " + command))
        success, error = try_handshake(self)
        self.serial_conn = success #added manually
        if not success:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Handshake failed: {error}"))
            return jsonify(result="False", error=str(error)), 500

        if self.serial_conn is None:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Connection lost after handshake."))
            return jsonify(result="False", error="Connection lost after handshake"), 500


        #connection was successful
        #Home the TR servo on the Swapper3D
        #rehome the ToolRotate servo #added Sep 3rd 2024 to try and address the repeatability issue of the TR servo
        perform_command(self, "hometoolrotate", False)
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Homed ToolRotate - after connect from try handshake"))


        # self._plugin_manager.send_plugin_message(self._identifier, dict(type="connectionState", message="Connected"))
        # time.sleep(3)
        # self._plugin_manager.send_plugin_message(self._identifier, dict(type="connectionState", message="Ready to Swap!"))
        return jsonify(result=str(success))

    elif command == "send":
        message = data.get("message")

        try:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Sending message: {message}"))
            self.serial_conn.write(message.encode())
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Message sent."))
        except Exception as e:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Failed to send message: {str(e)}"))
            return jsonify(result="False", error=str(e)), 500

        return jsonify(result="True")

    elif command == "disconnect":
        if self.serial_conn is not None:
            try:
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Disconnecting."))
                self.serial_conn.close()
                self.serial_conn = None
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Disconnected."))
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="connectionState", message="Disconnected"))
            except Exception as e:
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Failed to disconnect: {str(e)}"))
                return jsonify(result="False", error=str(e)), 500
        else:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="No connection to close."))
            return jsonify(result="False", error="No connection to close."), 500

        return jsonify(result="True")

    elif command == "retrieveFirmwareVersion":
        if self.serial_conn is not None:
            try:
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Retrieving Firmware Version."))
                retrieveFirmwareVersion(self)
            except Exception as e:
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Failed to retrieveFirmwareVersion: {str(e)}"))
                return jsonify(result="False", error=str(e)), 500
        else:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Must be connected to Swapper3D to retrieve the firmware version."))
            return jsonify(result="False", error="Must be connected to Swapper3D to retrieve the firmware version."), 500

        return jsonify(result="True")

    elif command == "load_insert":
        if self.insertLoaded:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Insert is already loaded; Must unload first."))
            return

        try:
            # Debug log: Print the raw 'insert_number' value received
            data = request.json
            command = data.get("command")
            insert_number = data.get("insert_number")
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"on_gcode_received.->Insert number:{insert_number}"))
            self.loadThisInsert = insert_number
                       
            HomeAxis = True 
            current_z = 0 
            PreparePrinterForSwap(self, current_z, HomeAxis, "readyForLoadInsert")
            
        # Ensure 'insert_number' is an integer
        except ValueError:
            # If 'insert_number' cannot be converted to an integer, log an error and return
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Invalid insert_number: cannot convert to integer"))
            return jsonify(result="False", error="Invalid insert_number: cannot convert to integer"), 400
            
        return jsonify(result="True")
        
    elif command == "unload":
        if not self.insertLoaded:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Insert is not already loaded; Must load first."))
            return   

        self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Received command: " + command))
        try:
            HomeAxis = True 
            current_z = 0 
            PreparePrinterForSwap(self, current_z, HomeAxis, "readyForUnload")
        except Exception as e:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Exception during unload: {str(e)}"))
            return jsonify(result="False", error=str(e)), 500

        self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Unload successful"))
        return jsonify(result="True")

    elif command == "borealignon":
        try:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Received command: " + command))
            #The bore alignment and swaps can only occur after the printer is in position. 
            #The only way to check if the printer is in position is to send a G1 -> G4 -> M118 "Message", 
            #then listen for incoming messages from the printer, When the "Message" is received then all the movement 
            #commands in the printer queue have completed and a swap can commence.
            
            HomeAxis = True  # Assuming you want to Home Axis when borealignon command is received
            current_z = 0  # Assuming the Z-position is 0 at this point
            PreparePrinterForSwap(self, current_z, HomeAxis, "readyForBoreAlignment")
            
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="connectionState", message="Bore alignment ON"))
            return jsonify(result="True")
        except Exception as e:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Exception during bore alignment on: {str(e)}"))
            return jsonify(result="False", error=str(e)), 500
        
    elif command == "borealignoff":
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Received command: " + command))
        try:
            success, error = bore_align_off(self)
            if not success:
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Bore alignment off failed: {error}"))
                return jsonify(result="False", error=str(error)), 500
        except Exception as e:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Exception during bore alignment off: {str(e)}"))
            return jsonify(result="False", error=str(e)), 500

        self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Bore alignment off successful"))
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="connectionState", message="Ready to Swap!"))
    
        return jsonify(result="True")

    else:
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Command not recognized: {command}"))
        return jsonify(result="False", error="Command not recognized."), 500
