import os
import time
from datetime import datetime
import traceback

def get_valid_gcode_settings(_settings, key, logger):
    settings_gcode = _settings.get([key])
    if settings_gcode is None:
        logger.info(f"No settings found. settings_gcode is {settings_gcode}")
        return None
    result_gcode = settings_gcode.strip().split("\n")
    return result_gcode


def inject_gcode(command, _settings, initial_tool_load, tool_change_occurred, logger, log_file_path):
    result_gcode = []
    stripped_line = command.strip()

    # Step 1: Inject "beforeStartGcode"
    if not initial_tool_load and (stripped_line.startswith("T") or "; select extruder" in command):
        start_gcode = get_valid_gcode_settings(_settings, "beforeStartGcode", logger)
        if start_gcode is not None:
            result_gcode.extend(start_gcode)
        result_gcode.append(command)
        initial_tool_load = True

    # Step 2: Inject "initialToolLoadGcode"
    elif not initial_tool_load and (stripped_line.startswith("T") or "; select extruder" in command):
        load_gcode = get_valid_gcode_settings(_settings, "initialToolLoadGcode", logger)
        if load_gcode is not None:
            result_gcode.extend(load_gcode)
        initial_tool_load = True

    # Step 3: Inject "toolChangeGcode"
    elif initial_tool_load and stripped_line.startswith("T"):
        change_gcode = get_valid_gcode_settings(_settings, "toolChangeGcode", logger)
        if change_gcode is not None:
            result_gcode.extend(change_gcode)

    # Step 4: Inject "beforeEndGcode"
    elif tool_change_occurred and (";TYPE:Custom" in command or "; Filament-specific end gcode" in command or "; park" in command):
        end_gcode = get_valid_gcode_settings(_settings, "beforeEndGcode", logger)
        if end_gcode is not None:
            result_gcode.extend(end_gcode)
        tool_change_occurred = False

    else:
        result_gcode.append(command)

    # Save the injected gcode into a file
    try:
        with open(log_file_path, 'a') as f:
            for item in result_gcode:
                f.write(item + '\n')
    except Exception as e:
        logger.error(f"Error saving gcode to file: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception traceback: {traceback.format_exc()}")
    return result_gcode, initial_tool_load, tool_change_occurred
