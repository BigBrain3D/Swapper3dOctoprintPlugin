# Octoprint plugin name: Swapper3D, File: __init__.py, Author: BigBrain3D, License: AGPLv3
import os
import time
import octoprint.plugin
import serial
import threading
from .commands import handle_command
from .gcode_injector import inject_gcode
from .default_settings import get_default_settings
from .Swap_utils import PreparePrinterForSwap, bore_align_on, bore_align_off, swap
from .Swapper3D_utils import load_insert, unload_insert, unload_filament, Stow_Wiper, try_handshake

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
        self.hasStartGcodeRun = False #custom flag to track if we already injected the start print commands needed for the swapper
        self.isPrintStarted = False #custom flag to track if we already injected the start print commands needed for the swapper
        self.isPrintDone = False #custom flag to track if we already injected the start print commands needed for the swapper
        self.current_extruder = None  # Initialize current_extruder as None
        self.next_extruder = None  # Initialize next_extruder as None
        self.insertLoaded = False
        self.loadThisInsert = None #used to pass the requested manual load insert number
        self.SwapInProcess = False #when true then don't start another swap
        self.InitialLoadComplete = False #because the currently loaded insert is zero(0) we need this value to know if the first initial tool load has been done
        self.currentTargetTemp = 0 #used to remember any temp that is set before a swap so that it can be returned to that temp after the swap completes
        self.current_fan_speed = 0 #used to remember if the fan was on and to turn it off while swapping and restore it after swap is complete
        self.extrusionSinceLastSwap = 0 #used to prevent a swap unless the extusion is at least the min from settings. reset in Swap_utils.swap()


    def on_event(self, event, payload):
        self._logger.info(f"event triggered: {event}")
        
        if event == "PrintStarted":
            
            # Create a new log file for each print.
            self.log_file_path = os.path.join(os.path.dirname(__file__), 'gcode', f'gcode_{int(time.time())}.txt')
            os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
            self._logger.info("Created a new log file at start of print: " + self.log_file_path)
            self.isPrintStarted = True
            self.is_print_done = False

        if event == "PrintDone":
            # The print has finished
            self._logger.info("The print job has finished")
            self.isPrintStarted = False
            self.hasStartGcodeRun = False
            self.is_print_done = True
            
        if event == "Connected":
            self._logger.info("Printer connection established.")
            # Take other actions as necessary
            self.runStartGcode();
            
    def on_after_startup(self):
        self._logger.info("Swapper3D plugin has started!")
        success, error = try_handshake(self)
        self.serial_conn = success

    def runStartGcode(self):
        # If the print has not started yet,
        if not self.hasStartGcodeRun:
            # Get the motor current setting 
            z_motor_current = self._settings.get(["zMotorCurrent"])

            # Log the setting value
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Setting motor current to {z_motor_current}"))

            # Set the motor current on the printer
            gcode_commands = [f"M906 {z_motor_current}"]
            self._printer.commands(gcode_commands)

            # Indicate that the print has started
            self.hasStartGcodeRun = True
            
            
    def get_e_value_from_cmd(self, cmd):
        try:
            parts = cmd.split(" ")
            for part in parts:
                if part.startswith("E"):
                    return float(part[1:])
        except ValueError:
            pass
        return None

    #this is gcode placed into the queue BEFORE sending to the printer
    #perhaps should be "return cmd," ??
    #cmd contains the entire line BUT we can't intercept comments, BUT we can send any text and it will output on the cmd as long as there is no semi-colon in front of the text
    #don't send commands to the printer in here. It will get stuck and freeze the whole plugin
    def hook_gcode_queuing(self, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None, *args, **kwargs):        
        #show all queued commands
        # self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"hook_gcode_queuing.cmd:{cmd}"))
        # self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"hook_gcode_queuing.SwapInProcess:{self.SwapInProcess}"))
        
        try:        
            #sum all extrusion
            #extrusionSinceLastSwap
            if (cmd.startswith("G1") or cmd.startswith("G0")):
                e_value = self.get_e_value_from_cmd(cmd)
                if e_value is not None:
                    self.extrusionSinceLastSwap += e_value
                    # self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"hook_gcode_queuing.E value increased:{self.extrusionSinceLastSwap}"))
            
            #remember the current hotend temperature
            if ((cmd.startswith("M109")
                or cmd.startswith("M104"))
                and not self.SwapInProcess):
                self.currentTargetTemp = cmd.split("S")[1]
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Temp recorded:{self.currentTargetTemp}"))
                
            #remember the current fan speed
            if (cmd.startswith("M106")
                and not self.SwapInProcess):
                self.current_fan_speed = cmd.split("S")[1]
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Fan speed recorded:{self.current_fan_speed}"))
                
            #remember if the fan is turned off
            if (cmd.startswith("M107")
                and not self.SwapInProcess):
                self.current_fan_speed = "0"
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Fan turned off (recorded)"))
                
            #we're looking at cmd not gcode now, and if there isn't anything there then a tool change cannot be triggered
            # #if there is no gcode then return
            # if not gcode: 
                # # self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"not gcode"))
                # return

            #Do we care if it's not printing? NO 
            # if not comm_instance.isPrinting():
                # return
                
            if (cmd.startswith("T") 
                and self.SwapInProcess):
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Tool change command sent while in Swap"))
                
                NozzleWipe = self._settings.get(["NozzleWipe"])
                #if NozzleWipe == False then resume here
                #otherwise swap is resumed in Swapper3D_utils.Stow_Wiper()
                if not NozzleWipe:
                    self.SwapInProcess = False
                    self._printer.commands("@resume")
                                
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"*****Swap_utils.swap().Swap complete - self.SwapInProcess{self.SwapInProcess}*****"))
                
                return
                
            if (cmd.startswith("M702") 
                and self.SwapInProcess):
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Filament unload command sent while in Swap"))
                self.SwapInProcess = False
                self._printer.commands("@resume")
                return
            
            # If the command is a tool change command (starts with "T")
            if (cmd.startswith("T") 
            and not self.SwapInProcess):
                if not comm_instance.isOperational():
                    self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Printer is not connected"))
                    return
                
                if self.serial_conn is None:
                    # self._logger.info("Swapper3D is disconnected")
                    self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Swapper3D is disconnected"))
                    return
            
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"hook_gcode_queuing.Processing tool change cmd:{cmd}"))
                # self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"gcode: {gcode}"))
                # self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"cmd: {cmd}"))
                # self._logger.info("Processing tool change command")
                          

                # Update the next extruder based on the command
                self.next_extruder = cmd[1:]
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"queue.Current extruder: {self.current_extruder}"))
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"queue.Next extruder: {self.next_extruder}"))
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"hasStartGcodeRun: {self.hasStartGcodeRun}"))


                # If the current and next extruders are the same
                # if the initial load is not complete and the current ext is not none then skip this guard
                #, log the corresponding message and return
                if (self.InitialLoadComplete 
                and self.current_extruder is not None 
                and self.current_extruder == self.next_extruder):
                    self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Current and next Tools are the same AND the initial load is complete. Skipping swap."))
                    return None #make sure that the tool change doesn't happen. If it did the filament would be pulled, uncut, from the quickswap insert

                #Stop the Swap if the filament extuded 
                #since the last swap is less than the minimum
                MinExtrusionBeforeSwap = int(self._settings.get(["MinExtrusionBeforeSwap"]))
                if (self.InitialLoadComplete 
                and self.current_extruder is not None 
                and self.extrusionSinceLastSwap < MinExtrusionBeforeSwap):
                    self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Prevented swap because of too short extusion: {self.extrusionSinceLastSwap}"))
                    return None #not enough extrusion to get the filament into the insert, so prevent this tool change, otherwise the filament will get pulled out and jam the print head


                # Initialize current_z outside the try block
                current_z = 0
                
                #if the printer is printing then assume that it's already been homed
                #otherwise it's probably a manually issued T command and then the printer should be homed Just to be safe
                if comm_instance.isPrinting():
                    HomeAxis = False
                    
                    #only try to get the current Z during a print
                    #otherwise the Tool command was sent manually
                    #and the printer will be homed
                    #which means that the Z will be zero(0) and the Z needs to be moved up to 95
                    try:
                        # Get the current Z position of the printer
                        current_z = self._printer.get_current_data()["currentZ"]
                        
                        # If obtained Z position is None, set it to 0
                        if current_z is None:
                            current_z = 0
                    except Exception as e:
                        # Handle or log any exceptions that occurred while getting current_z
                        self._plugin_manager.send_plugin_message(f"Exception occurred while getting current Z position: {e}")
                else:
                    #should ALWAYS be true becuase the users could have moved the Z position manually between the load and subsequent load/unloads
                    HomeAxis = True
                


                # Send the current Z position to the plugin manager
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="current_z", message=str(current_z)))

                # Prepare the printer for the swap
                self.SwapInProcess = True
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Enqueue Paused"))
                self._printer.commands("@pause")
                # self._printer.pause_print() #don't need this
                
                thread = threading.Thread(target=PreparePrinterForSwap, args=(self, current_z, HomeAxis, "readyForSwap")) 
                thread.start()
                
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"T{self.next_extruder} command intercepted"))
                return None #prevent the T command from being issued to the printer. It will be sent from the swap method
                
            if  (not self.SwapInProcess
                and ("M73 Q100" in cmd
                    or cmd.startswith("M702"))):
                            
                HomeAxis = False #set to False for production
                current_z = 0
                try:
                    # Get the current Z position of the printer
                    current_z = self._printer.get_current_data()["currentZ"]
                    
                    # If obtained Z position is None, set it to 0
                    if current_z is None:
                        current_z = 0
                except Exception as e:
                    # Handle or log any exceptions that occurred while getting current_z
                    self._plugin_manager.send_plugin_message(f"Exception occurred while getting current Z position: {e}")
            
                #send command "unload" to commands.py handle_command
                self.SwapInProcess = True
                self._printer.commands("@pause")
                
                thread = threading.Thread(target=PreparePrinterForSwap, args=(self, current_z, HomeAxis, "readyForFilamentUnload")) 
                thread.start()
                return None #"Filament Unload command intercepted" #prevent the unload command from being sent to the printer. It will be sent from the unload command
                

        except Exception as e:
            # If an error occurs, log the error message
            self._logger.error(f"An error occurred in hook_gcode_queuing: {str(e)}")
            
            # Also log the stack trace of the error
            self._logger.error(traceback.format_exc())

        # Returns the command unmodified
        return

    #this is gcode FROM THE PRINTER
    def on_gcode_received(self, comm, line, *args, **kwargs):
        #show all received commands
        # if (not line.startswith("T:")
            # and not line == ""):
            # self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"on_gcode_received.line:{line}"))

        #this prevents Octoprint from automatically reverting the tool when it sends a T0 command
        if "Invalid extruder" in line:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Tool reversion stopped"))
            return None
            
        # Check if the line contains our echo (case insensitive)
        if "readyForBoreAlignment" in line:
            # Finally, turn on bore alignment
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="command echo from printer: borealignon"))
            try:            
                success, error = bore_align_on(self)
                
                # self._printer.commands("@resume")

                if not success:
                    self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Bore alignment on failed: {error}"))
            except Exception as e:
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Exception during bore alignment on: {str(e)}"))
            
            return line

        if "readyForSwap" in line:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="command echo from printer: readyforswap"))
            
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"on_gcode_received.Current extruder: {self.current_extruder}"))
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"on_gcode_received.Next extruder: {self.next_extruder}"))
            
            if self.next_extruder is not None: # Add a pre-check for next_extruder
                try:                    
                
                    thread = threading.Thread(target=swap, args=(self,)) 
                    thread.start()                    

                except Exception as e:
                    self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Exception during Swap: {str(e)}"))
            else:
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Next extruder not set. Swap operation not executed."))

            return line
                
        if "readyForLoadInsert" in line:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="command echo from printer: readyForLoad Insert"))
            
            thread = threading.Thread(target=load_insert, args=(self, self.loadThisInsert)) 
            thread.start()
            
            # load_insert(self, self.loadThisInsert)
            return line
            
        if "readyForUnload" in line:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="command echo from printer: readyForUnload"))
            
            thread = threading.Thread(target=unload_insert, args=(self,)) 
            thread.start()
            
            # unload_insert(self)
            return line
                
        if "readyForFilamentUnload" in line:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="command echo from printer: readyForUnloadFilament"))
                        
            thread = threading.Thread(target=unload_filament, args=(self,)) 
            thread.start()
            
            return line
            
        if "StowWiper" in line:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="command echo from printer: readyForUnloadFilament"))
                        
            thread = threading.Thread(target=Stow_Wiper, args=(self,)) 
            thread.start()
            
            return line
            
        return line
            
    def get_template_configs(self):
        return [
            {"type": "settings", "custom_bindings": False}
        ]

    def get_assets(self):
        return {"js": ["js/Swapper3D_ViewModel.js"]}
        
    @octoprint.plugin.BlueprintPlugin.route("/command", methods=["POST"])
    def handle_blueprint_command(self):
        result = handle_command(self)
        if result is None:
            return "No response", 400  # Return a 400 Bad Request if no response
        return result  # Ensure that you return whatever handle_command returns

    def is_blueprint_csrf_protected(self):
        return True
        
    def get_settings_defaults(self):
        default_settings = get_default_settings()
        self._logger.debug(f"Default settings: {default_settings}")
        return default_settings

    def get_update_information(self):
        return dict(
            Swapper3D=dict(
                displayName="Swapper3D",
                displayVersion=self._plugin_version,
                type="github_release",
                user="BigBrain3D",
                repo="Swapper3dOctoprintPlugin",
                current=self._plugin_version,
                pip="https://github.com/BigBrain3D/Swapper3dOctoprintPlugin/archive/{target_version}.zip",
                pip_args=["--no-cache-dir", "--ignore-installed", "--force-reinstall"]
            )
        )


__plugin_name__ = "Swapper3D"
__plugin_version__ = "0.3.5" 
__plugin_description__ = "An Octoprint plugin for Controlling the Swapper3D"
__plugin_author__ = "BigBrain3D"
__plugin_url__ = "https://github.com/BigBrain3D/Swapper3dOctoprintPlugin"
__plugin_license__ = "AGPLv3"
__plugin_pythoncompat__ = ">=3.7,<4"  # Compatible python versions
__plugin_implementation__ = Swapper3DPlugin()

def __plugin_load__():
    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.comm.protocol.gcode.received": __plugin_implementation__.on_gcode_received,
        "octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.hook_gcode_queuing,
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.event.EventHandler": __plugin_implementation__.on_event
    }
    
def get_update_hooks(self):
    return {
        "octoprint.plugin.softwareupdate.check_config": self.get_update_information
    }