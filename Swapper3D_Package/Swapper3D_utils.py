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
def perform_command(plugin, command, WaitForOk=True):
    # Send the command with parity to the Swapper3D device
    write_message_with_parity(plugin, command)
    time.sleep(1)

    if not WaitForOk:
        # Log that we are sending the command without waiting for an "ok" response
        send_plugin_message(plugin, f"2A.Sending command {command} to Swapper3D. NOT waiting for OK")
        return True, None

    # Construct the expected response string, which should match the command followed by "_ok"
    expected_response_prefix = f"{command}_ok"
    
    while True:
        # Read and check the response from the device
        check_response, response_without_parity = read_and_check_response(plugin)

        # Debugging the full original response (including the parity bit)
        # send_plugin_message(plugin, f"Full Response: [{response_without_parity}]")

        # If the response is empty, continue reading until a valid response is received
        if check_response is None:
            continue
        elif check_response:
            # Log the actual response received and compare it to the expected response
            # comparison_result = "same" if response_without_parity == expected_response_prefix else "not the same"
            
            # Log the character-by-character comparison
            response_chars = ' '.join(f"[{ord(c)}]" for c in response_without_parity)
            # expected_chars = ' '.join(f"[{ord(c)}]" for c in expected_response_prefix)

            # debug_message = (
                # f"Received: [{response_without_parity}] "
                # f"compared to Expected: [{expected_response_prefix}] - {comparison_result}\n"
                # f"Response chars: {response_chars}\n"
                # f"Expected chars: {expected_chars}"
            # )
            # send_plugin_message(plugin, debug_message)
            
            send_plugin_message(plugin, response_chars)

            # If the response matches the expected command-specific 'ok', log success and return
            if response_without_parity == expected_response_prefix:
                send_plugin_message(plugin, f"2B.Command '{command}' succeeded.")
                return True, None
        else:
            # Log if the parity check failed and return an error
            send_plugin_message(plugin, f"2C.Command '{command}' failed.")
            return False, "Parity check did not pass."






def retrieveFirmwareVersion(plugin):
    command = "RetrieveCurrentFirmwareVersion"
    send_plugin_message(plugin, "Sending command to RetrieveCurrentFirmwareVersion")
    return perform_command(plugin, command)

def load_insert(plugin, insert_number):
    # Check the printer is connected
    if not plugin._printer.is_operational():
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="Printer must be connected to Swap!"))
        return "Printer not connected" 

    command = f"load_insert{insert_number}"
    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Sending command to load_insert insert {insert_number}"))

    
    if perform_command(plugin, command):
        #updated Aug 17th 2024 makes the "Currently loaded insert" text box in the Swapper3D tab show the same number as the sticker on the tool holder wheel.
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"3.Aug23.Swapper3D_utils.load_insert: OK received? Successfully loaded insert: {str(int(insert_number) + 1)}"))
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="currentlyLoadedInsert", message=str(int(insert_number) + 1))) 

        
        plugin.insertLoaded = True
    else:
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Failed to load"))

    return True #"OK" updated Aug 23rd 2024

def unload_insert(plugin):
    # Check the printer is connected
    if not plugin._printer.is_operational():
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="Printer must be connected to Swap!"))
        return "Printer not connected" 

    UnloadSuccess = True # set to true here and False if there is an error somewhere in this method

    # Get the settings
    filamentSwitcherType = plugin._settings.get(["filamentSwitcherType"])
    extrudeSpeedPulldown = plugin._settings.get(["extrudeSpeedPulldown"])
    extrudeLengthLockingHeight = plugin._settings.get(["extrudeLengthLockingHeight"])
    extrudeLengthCuttingHeight = plugin._settings.get(["extrudeLengthCuttingHeight"])
    StockExtruderMaxFeedrate = plugin._settings.get(["StockExtruderMaxFeedrate"])
    SwapExtruderMaxFeedrate = plugin._settings.get(["SwapExtruderMaxFeedrate"])
    StockExtruderMaxAcceleration = plugin._settings.get(["StockExtruderMaxAcceleration"])
    SwapExtruderMaxAcceleration = plugin._settings.get(["SwapExtruderMaxAcceleration"])
    msDelayAfterExtrude = plugin._settings.get(["msDelayAfterExtrude"])
    msDelayPerDegreeMovedDuringSwapPulldown = plugin._settings.get(["msDelayPerDegreeMovedDuringSwapPulldown"])
    retractLengthAfterCut = plugin._settings.get(["retractLengthAfterCut"])
    retractSpeed = plugin._settings.get(["retractSpeed"])
    
    
    # palette settings
    extrudeSpeedPaletteCuts = plugin._settings.get(["extrudeSpeedPaletteCuts"])
    numPaletteCuts = plugin._settings.get(["numPaletteCuts"])
    lengthAdditionalCut = plugin._settings.get(["lengthAdditionalCut"])
    delayAfterCut = int(plugin._settings.get(["delayAfterCut"]))

    # Check if msDelayAfterExtrude is not None
    if msDelayAfterExtrude is not None:
        # Convert msDelayAfterExtrude to float
        delayAfterExtrude = float(msDelayAfterExtrude)

        # Send a message to the plugin with the delay time
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Delaying for {msDelayAfterExtrude} milliseconds before extruding..."))
    else:
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="msDelayAfterExtrude setting is not defined."))
        return

    # begin unload sequence
    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="Executing unload"))
        
    gcode_commands = ["M302 P1 ;allow cold extrusion",
                      f"M203 E{SwapExtruderMaxFeedrate}",
                      f"M201 E{SwapExtruderMaxAcceleration}"]
    plugin._printer.commands(gcode_commands)
            
    perform_command(plugin, "unload_connect")
    
    #pulldown to locking height
    # Extrude filament at the same time as the pulldown 
    #all these commands are sent to the printer at the same time
    #octoprint moves on but the printer tries to execute the commands
    #the first command is a delay/sleep/pause, which allow the Swapper3D to get a head start on the pulldown
    gcode_commands = [f"G4 P{delayAfterExtrude}",
                      "G92 E0 ;reset extrusion distance",
                      f"G1 E{extrudeLengthLockingHeight} F{extrudeSpeedPulldown}"]
    plugin._printer.commands(gcode_commands)
  
    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"msDelayPerDegreeMovedDuringSwapPulldown: {msDelayPerDegreeMovedDuringSwapPulldown}"))
    perform_command(plugin, f"unload_pulldown_lockingheight{msDelayPerDegreeMovedDuringSwapPulldown}")
    
    # pulldown to cutting height
    # Extrude filament at the same time as the pulldown 
    gcode_commands = [f"G4 P{delayAfterExtrude}",
                      "G92 E0 ;reset extrusion distance",
                      f"G1 E{extrudeLengthCuttingHeight} F{extrudeSpeedPulldown}"]
    plugin._printer.commands(gcode_commands)
   
    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"msDelayPerDegreeMovedDuringSwapPulldown: {msDelayPerDegreeMovedDuringSwapPulldown}"))
    perform_command(plugin, f"unload_pulldown_cuttingheight{msDelayPerDegreeMovedDuringSwapPulldown}")
    

    
    # whether it's Palette or MMU it always needs to cut and stow the insert
    #perform_command(plugin, "unload_deploycutter") #commented out on Sep 2nd updated so that command now takes an angle
#cut cycle
    perform_command(plugin, "cutter_open")
    perform_command(plugin, "unload_deploycutter120")
    perform_command(plugin, "cutter_cut")

      

    # palette multi cuts
    if filamentSwitcherType == "Palette":
        # move the tool arm out of the way a little so it's very quick
        perform_command(plugin, "unload_AvoidBin") #why is there a delay after this before the extrude?? In the firmware there is zero(0)ms delay so it should be instant.
        
        intNumPaletteCuts  = int(numPaletteCuts)

        # start palette cut loop
        for _ in range(intNumPaletteCuts):
#open
            perform_command(plugin, "cutter_open")

            # extrude
            gcode_commands = ["G92 E0 ;reset extrusion distance", 
                             f"G1 E{lengthAdditionalCut} F{extrudeSpeedPaletteCuts}"]
            plugin._printer.commands(gcode_commands)

            time.sleep(delayAfterCut/1000)

            # cut
#cut           
            perform_command(plugin, "cutter_cut")
        # end palette cut loop

#cut cycle
    # perform_command(plugin, "cutter_open")
    # perform_command(plugin, "unload_deploycutter123")
    # perform_command(plugin, "cutter_cut")
    
    # retract filament
    # Send the G-code commands to prepare for swap
 #break any string connection between insert and main filament strand
    gcode_commands = ["G92 E0 ;reset extrusion distance"
                     ,f"G1 E-10 F300"]
    plugin._printer.commands(gcode_commands)
    gcode_commands = ["G92 E0 ;reset extrusion distance"
                     ,f"G1 E{retractLengthAfterCut} F{retractSpeed}"]
    plugin._printer.commands(gcode_commands)

#wait for the retract to complete    
    #RetractDelay = int(lengthAdditionalCut)/(int(extrudeSpeedPaletteCuts)/60) + (10/(300/600))
    #plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"RetractDelay(sec): {RetractDelay}"))
    time.sleep(3) #seconds
#open
    perform_command(plugin, "cutter_open")
    
#stow cutter
    perform_command(plugin, "unload_stowCutter", True) #must be true. Failing to wait can cause an OK in the wrong spot

#used to retract filament here Sep 2nd 2023

    
    
    #commented out because the cutter guard is under the hotend for a long time and there is concern it could melt
    # perform_command(plugin, "unload_stowInsert", True)
    # perform_command(plugin, "unload_stowCutter")

    perform_command(plugin, "unload_stowInsert", True)


    if filamentSwitcherType == "Palette":
        perform_command(plugin, "unload_dumpWaste")  # Palette only.

#open
    #perform_command(plugin, "cutter_open") #commented out because it's wrecking the end effector
    
    # set the feedrate and acceleration back to Stock
    gcode_commands = ["M302 S170 ;disable cold extrusion",
                      f"M203 E{StockExtruderMaxFeedrate}",
                      f"M201 E{StockExtruderMaxAcceleration}"]
    plugin._printer.commands(gcode_commands)

    
    perform_command(plugin, "unloaded_message", False)#added Aug 16th 2024, reset the LCD message to "Ready to Swap!" and Insert "EMPTY"
    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"UnloadSuccess: {UnloadSuccess}"))

    if UnloadSuccess:        
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="currentlyLoadedInsert", message="Empty"))
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Swapped to insert: Empty"))

        plugin.insertLoaded = False
    else:
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="Failed to Unload"))

    #rehome the ToolRotate servo #added Sep 3rd 2024 to try and address the repeatability issue of the TR servo
    perform_command(plugin, "hometoolrotate", False)
    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Homed ToolRotate - after unload"))


    return True

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

def unload_filament(plugin):
    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="unload_filament called"))

    if plugin.insertLoaded:
        unload_insert(plugin)
    else:
        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="No insert in QuickSwap-Hotend. Unload Skipped."))
    
    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="sending M702 C back to queue"))
    gcode_commands = [f"M702 C ;Sent by Swapper3D_utils.unload_filament()"]
    plugin._printer.commands(gcode_commands)
    
    #plugin.SwapInProcess = False #cannot set to false here or it will cause an infinite loop
    return True
    
def Deploy_Wiper(plugin):
    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="Swapper3D_utils.Deploy_Wiper()"))
    perform_command(plugin, "wiper_deploy", True)
    return True
    
    
def Stow_Wiper(plugin):
    perform_command(plugin, "wiper_stow", True)
    
    #Restore the fan to its original speed
    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Swapper3D_utils.Stow_Wiper: Printer resumed. Setting fan speed to: {plugin.current_fan_speed}"))
    gcode_commands = [f"M106 S{plugin.current_fan_speed} ;restore fan speed",
                      "@resume"]
    plugin._printer.commands(gcode_commands)
    
    
    plugin.SwapInProcess = False
    plugin.extrusionSinceLastSwap = 0
    
    #rehome the ToolRotate servo #added Sep 3rd 2024 to try and address the repeatability issue of the TR servo
    perform_command(plugin, "hometoolrotate", False)
    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Homed ToolRotate - after wiper stowed"))

    
    return True
    
def try_handshake(plugin):
    # Identify the available Arduino ports. The list only includes ports with 'Arduino Uno' in their description.
    # This avoids connecting to other devices and interfering with the printer connection.
    arduino_ports = [port.device for port in serial.tools.list_ports.comports() if 'Arduino Uno' in port.description]

    # If no Arduino ports are found, return an error message.
    if not arduino_ports:
        return None, "No Swapper3D found. Are you sure the USB is plugged between the Swapper3D and Octoprint?"

    # Try to connect to each Arduino port found
    for port in arduino_ports:
        try:
            plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Trying to connect to port {port}..."))
            ser = serial.Serial(port, 9600, timeout=10)  # Increased the timeout to 10 seconds to account for slower Raspberry Pi responses.
            time.sleep(3)  # Allow some time for the connection to stabilize.

            connection_attempts = 3  # Allow 3 connection attempts
            while connection_attempts > 0:
                plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="Sending handshake message 'octoprint'..."))
                message = 'octoprint'
                parity_bit = parity_of(message)
                plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Parity bit for 'octoprint': {parity_bit}"))
                ser.write((message + str(parity_bit) + '\n').encode())
                time.sleep(3)

                read_attempts = 3  # Try to read the response up to 3 times with a 3-second delay between reads
                while read_attempts > 0:
                    time.sleep(3)  # Wait 3 seconds before trying to read the response
                    response = ser.readline().decode('utf-8').strip()
                    plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Received: {response}"))

                    if response:
                        # Split the received message and parity bit
                        response_message, response_parity_bit = response[:-1], response[-1]

                        # Calculate and check the parity of the received message
                        if parity_of(response_message) == int(response_parity_bit):
                            plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="Handshake successful!"))
                            plugin._settings.set(["serialPort"], port)
                            plugin._settings.set(["baudrate"], ser.baudrate)
                            plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="connectionState", message="Connected"))
                            time.sleep(3)
                            plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="connectionState", message="Ready to Swap!"))
                            return ser, None
                        else:
                            plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Parity check failed for message: {response_message}"))
                    else:
                        plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="No response received"))
                    
                    read_attempts -= 1  # Decrement the number of read attempts

                # After 3 read attempts, decrement the connection attempts
                connection_attempts -= 1

            plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message="Handshake failed, closing connection."))
            ser.close()
            return None, f"Failed to handshake with the device on port {port}. No valid response received after 3 read attempts"
        
        # If there is an error in connecting to the serial port, catch and log the exception
        except serial.SerialException as e:
            plugin._plugin_manager.send_plugin_message(plugin._identifier, dict(type="log", message=f"Failed to connect to {port}: {e}"))
    
    # If no ports are successfully connected, return a failure message.
    return None, "Failed to connect to any port"
