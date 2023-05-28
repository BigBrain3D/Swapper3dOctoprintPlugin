# Octoprint plugin name: Swapper3D, File: Swapper3D_utils.py, Author: BigBrain3D, License: AGPLv3
 
# Import required libraries
import serial
import serial.tools.list_ports
import time

def parity_of(input_string):
    """
    Function to calculate parity bit for a given string.

    :param input_string: String value to calculate parity for
    :return: Parity bit (0 or 1)
    """
    count = 0
    for ch in input_string:
        value = ord(ch)
        while value:
            count += 1
            value = value & (value - 1)
    return ~count & 1  # returns 1 for odd parity, 0 for even parity


def check_parity(plugin, message):
    received_parity_bit = int(message[-1])  # extract the last character from the message
    message_without_parity_bit = message[:-1]
    calculated_parity_bit = parity_of(message_without_parity_bit)
    
    if received_parity_bit != calculated_parity_bit:
        plugin._plugin_manager.send_plugin_message(
            plugin._identifier, 
            dict(type="log", message=f"Parity check failed for message: {message_without_parity_bit}")
        )
        return False
    else:
        plugin._plugin_manager.send_plugin_message(
            plugin._identifier, 
            dict(type="log", message=f"Parity check passed for message: {message_without_parity_bit}")
        )
        return True


def try_handshake(plugin):
    arduino_ports = [port.device for port in serial.tools.list_ports.comports() if 'Arduino Uno' in port.description]
    other_ports = [port.device for port in serial.tools.list_ports.comports() if 'Arduino Uno' not in port.description]
    all_ports = arduino_ports + other_ports

    for port in all_ports:
        try:
            plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Trying to connect to {port}..."))
            ser = serial.Serial(port, 9600, timeout=2)
            time.sleep(2)

            attempts = 3
            while attempts > 0:
                plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="Sending handshake message 'Octoprint'..."))
                message = 'octoprint'
                parity_bit = parity_of(message)
                plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Parity bit for 'Octoprint': {parity_bit}"))
                ser.write((message + str(parity_bit) + '\n').encode())
                time.sleep(1)

                response = ser.readline().decode('utf-8').strip()
                plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Received: {response}"))

                # Split the received message and parity bit
                response_message, response_parity_bit = response[:-1], response[-1]

                # Calculate and check parity of received message
                if parity_of(response_message) == int(response_parity_bit):
                    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="Handshake successful!"))
                    plugin._settings.set(["serialPort"], port)
                    plugin._settings.set(["baudrate"], ser.baudrate)
                    return ser, None
                else:
                    attempts -= 1
                    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Parity check failed for message: {response_message}"))

            plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="Handshake failed, closing connection."))
            ser.close()
            return None, f"Failed to handshake with the device on port {port}. Parity check failed for response after 3 attempts"
        except serial.SerialException as e:
            plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Failed to connect to {port}: {e}"))
    return None, "Failed to connect to any port"



def swap_to_insert(plugin, insert_number):
    try:
        swap_command = f"swap{insert_number}"
        
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Sending command to swap to insert {insert_number}"))
        
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Serial connection {plugin.serial_conn}"))
        
        message = swap_command
        parity_bit = parity_of(message)
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Parity bit for '{swap_command}': {parity_bit}"))
        plugin.serial_conn.write((message + str(parity_bit) + '\n').encode())  # Use the serial connection saved in plugin
        time.sleep(1)

        # Retry up to 3 times if the parity of the incoming message fails
        attempts = 0
        while attempts < 3:
            response = plugin.serial_conn.readline().decode('utf-8').strip()  # Use the serial connection saved in plugin
            plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Received: {response}"))

            if check_parity(plugin, response):
                if response[:-1].startswith("ok"):
                    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Swap to insert {insert_number} was successful."))
                    return True, None
                else:
                    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Swap to insert failed with response: {response}"))
                    return False, response
            attempts += 1

        # If reached here, all attempts failed.
        error_message = "All attempts failed, parity check did not pass."
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=error_message))
        return False, error_message

    except Exception as e:
        error_message = str(e)
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Failed to swap to insert: {error_message}"))
        return False, error_message

def unload_insert(plugin):
    try:
        unload_command = "unload"

        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="Sending command to unload"))

        message = unload_command
        parity_bit = parity_of(message)
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Parity bit for '{unload_command}': {parity_bit}"))
        plugin.serial_conn.write((message + str(parity_bit) + '\n').encode())
        time.sleep(1)

        # Retry up to 3 times if the parity of the incoming message fails
        attempts = 0
        while attempts < 3:
            response = plugin.serial_conn.readline().decode('utf-8').strip()
            plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Received: {response}"))

            if check_parity(plugin, response):
                if response[:-1].startswith("ok"):
                    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="Unload was successful."))
                    return True, None
                else:
                    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Unload failed with response: {response}"))
                    return False, response
            attempts += 1

        # If reached here, all attempts failed.
        error_message = "All attempts failed, parity check did not pass."
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=error_message))
        return False, error_message

    except Exception as e:
        error_message = str(e)
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Failed to unload: {error_message}"))
        return False, error_message
