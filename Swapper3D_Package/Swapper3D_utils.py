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

def send_plugin_message(plugin, message):
    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=message))

def check_parity(plugin, message):
    received_parity_bit = int(message[-1])  # extract the last character from the message
    message_without_parity_bit = message[:-1]
    calculated_parity_bit = parity_of(message_without_parity_bit)
    
    if received_parity_bit != calculated_parity_bit:
        send_plugin_message(plugin, f"Parity check failed for message: {message_without_parity_bit}")
        return False
    else:
        #send_plugin_message(plugin, f"Parity check passed for message: {message_without_parity_bit}")
        return True

# Write a message with parity to the serial connection
def write_message_with_parity(plugin, message):
    parity_bit = parity_of(message)
    send_plugin_message(plugin, f"Parity bit for '{message}': {parity_bit}")
    plugin.serial_conn.write((message + str(parity_bit) + '\n').encode())

# Read a response from the serial connection and check its parity
def read_and_check_response(plugin):
    response = plugin.serial_conn.readline().decode('utf-8')
    print(f"Raw response: {repr(response)}")
    
    # Check if the response is a complete line
    if not response.endswith('\n'):
        print("Incomplete response received, ignoring.")
        return None, None

    response = response.strip()

    # Check if the response is not empty before attempting to check the parity
    if response:
        received_parity_bit = int(response[-1])  # extract the last character from the message
        message_without_parity_bit = response[:-1]
        calculated_parity_bit = parity_of(message_without_parity_bit)

        if received_parity_bit != calculated_parity_bit:
            send_plugin_message(plugin, f"Parity check failed for message: {response}")
            return False, None
        else:
            return True, message_without_parity_bit
    else:
        send_plugin_message(plugin, "Received empty response")
        return None, None




# Abstract the common operations of swap_to_insert and unload_insert into one function
def perform_command(plugin, command):
    write_message_with_parity(plugin, command)
    time.sleep(1)

    send_plugin_message(plugin, f"Sending command {command} to Swapper3D")

    # Keep reading responses until an OK is received
    while True:
    
        check_response, response = read_and_check_response(plugin)

        # If the response is empty, continue reading responses
        if check_response is None:
            continue
        elif check_response:
            send_plugin_message(plugin, response)
            if response and response.startswith("ok"):
                return True, None
        else:
            send_plugin_message(plugin, f"Command '{command}' failed.")
            return False, "Parity check did not pass."



def load_insert(plugin, insert_number):
    command = f"load_insert{insert_number}"
    send_plugin_message(plugin, f"Sending command to load_insert insert {insert_number}")
    return perform_command(plugin, command)

def unload_insert(plugin):
    # Check the printer is connected
    if not plugin._printer.is_operational():
        send_plugin_message(plugin, "Printer must be connected to Swap!")
        return "Printer not connected" 

    #Commented for testing
    #uncomment for production
    # # Check the hotend temperature
    # hotend_temp = plugin._printer.get_current_temperatures()['tool0']['actual']
    # if hotend_temp < 200:
        # send_plugin_message(plugin, "Hotend temperature is less than 200C")
        # return "Hotend too cold to Swap!" 
    
    # Get the setting
    filamentSwitcherType = plugin._settings.get(["filamentSwitcherType"])

    if filamentSwitcherType != "Palette":
        send_plugin_message(plugin, "Executing Parallel unload")
        
        perform_command(plugin, "unload_connect")
        
        perform_command(plugin, "unload_pulldown_lockingheight")

        #locking height
        # Extrude filament at the same time as the pulldown 
		#was F3960
        gcode_commands = ["G92 E0 ;reset extrusion distance"
                         ,"G1 E5.000 F5000.0"] 
        plugin._printer.commands(gcode_commands)
        
        time.sleep(1)

        #cutting height
        perform_command(plugin, "unload_pulldown_cuttingheight")
        gcode_commands = ["G92 E0 ;reset extrusion distance"
                         ,"G1 E55.000 F5000.0"] 
        plugin._printer.commands(gcode_commands)
        
        
       # perform_command(plugin, "unload_deploycutter")
       # perform_command(plugin, "unload_cut")
       # perform_command(plugin, "unload_stowInsert")
        
        # retract filament
        # Send the G-code commands to prepare for swap
        # gcode_commands = ["G92 E0 ;reset extrusion distance"
                         # ,"G1 E-70.000 F3960.0"]
        
        # plugin._printer.commands(gcode_commands)
        # perform_command(plugin, "unload_stowCutter")
        
    else:
        send_plugin_message(plugin, "Executing Serial unload")
        
        perform_command(plugin, "unload_connect")
        perform_command(plugin, "unload_pulldown")
        
        # The printer is told to extrude here. You need to implement this functionality.
        # Extrude filament at the same time as the pulldown
        gcode_commands = ["G92 E0 ;reset extrusion distance"
                         ,"G1 E55.000 F3960.0"]
        plugin._printer.commands(gcode_commands)
        
        
        perform_command(plugin, "unload_deploycutter_guide") #palette only
        perform_command(plugin, "unload_deploycutter")
        perform_command(plugin, "unload_cut")
        perform_command(plugin, "unload_stowInsert")
        #extrude then cut    #palette only
        
        #retract filament
        # Send the G-code commands to prepare for swap
        gcode_commands = ["G92 E0 ;reset extrusion distance"
                         ,"G1 E-70.000 F3960.0"]
        
        plugin._printer.commands(gcode_commands)
        perform_command(plugin, "unload_stowCutter")
        perform_command(plugin, "unload_dumpWaste")  # Palette only.

    return "OK"  # Return OK if all commands were successfully executed.


def get_firmware_version(plugin):
    version_parts = []
    for command in ["readmajor", "readminor", "readpatch"]:
        result, error = perform_command(plugin, command)
        if result:
            version_part = plugin.serial_conn.readline().decode('utf-8').strip()[:-1]
            version_parts.append(version_part)
        else:
            send_plugin_message(plugin, f"Failed to get part of firmware version with command '{command}': {error}")
            return None, error

    return '.'.join(version_parts), None



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
                plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="Sending handshake message 'octoprint'..."))
                message = 'octoprint'
                parity_bit = parity_of(message)
                plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Parity bit for 'octoprint': {parity_bit}"))
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

