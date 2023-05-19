# Octoprint plugin name: Swapper3D, File: commands.py, Author: BigBrain3D, License: AGPLv3

from flask import request, jsonify
from .Swapper3D_utils import try_handshake  # import the try_handshake function

def handle_command(self):
    data = request.json
    command = data.get("command")

    if command == "connect":
        # Check if a connection already exists
        if self.serial_conn is not None:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="A connection is already established. Disconnect before attempting a new connection."))
            return jsonify(dict(success=False, error="A connection is already established. Disconnect before attempting a new connection.")), 500

        # Send a plugin message to update the "Swapper3DLog" textarea
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Received command: " + command))

        # call the try_handshake function when the connect command is received
        serial_conn, error = try_handshake(self)

        if serial_conn is None:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Handshake failed: {error}"))
            return jsonify(dict(success=False, error=error)), 500
        else:
            # Save the serial connection object
            self.serial_conn = serial_conn
            if self.serial_conn is None:
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Connection lost after handshake."))
                return jsonify(dict(success=False, error="Connection lost after handshake")), 500
            else:
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="connectionState", message="Connected"))
                return jsonify(dict(success=True))

    elif command == "send":
        message = data.get("message")
        try:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Sending message: {message}"))
            self.serial_conn.write(message.encode())
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Message sent."))
        except Exception as e:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Failed to send message: {str(e)}"))
            return jsonify(success=False, error=str(e)), 500

        return jsonify(success=True)

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
                return jsonify(success=False, error=str(e)), 500
        else:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="No connection to close."))
            return jsonify(success=False, error="No connection to close."), 500

        return jsonify(success=True)

    return jsonify(success=False), 400
