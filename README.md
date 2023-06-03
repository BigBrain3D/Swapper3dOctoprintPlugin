# Swapper3D_Octoprint_Plugin
The first Octoprint plugin for synchronizing a 3D printer with the Swapper3D


This OctoPrint plugin, named Swapper3D, is designed to manage a 3D printer tool head swapping mechanism by the same name. The plugin provides control, status monitoring, and log tracking for the Swapper3D device. Here's a summary of what each file contributes:

1. `Swapper3D_utils.py` provides utility functions for serial communication between OctoPrint and the Swapper3D device, such as establishing a handshake, swapping the tool head, and unloading the tool head.

2. `Swapper3D_ViewModel.py` is the ViewModel for the Swapper3D plugin. This file is responsible for defining and controlling the user interface behaviors such as displaying logs, displaying the connection state, managing the commands when buttons are clicked, and handling plugin messages. It also handles sending AJAX requests to the plugin's back-end.

3. `Swapper3D_tab.jinja2` is a Jinja2 template for the main tab of the Swapper3D plugin on OctoPrint's interface. It includes the interface for the connection status, the current loaded insert, a dropdown for selecting an insert, an unload button, a log display, and also some buttons to connect and disconnect the device.

4. `Swapper3D_settings.jinja2` is a Jinja2 template for the plugin's settings in OctoPrint's settings interface. It allows the user to specify the X, Y, Z coordinates and the gcode for the tool change location.

5. `setup.py` is the setup file for the plugin, including the basic metadata about the plugin and its dependencies.

6. `__init__.py` is the main file of the plugin, where the Swapper3DPlugin class is defined. This class initializes the plugin, manages the settings, assets, and templates, handles commands sent through the blueprint route, and implements an event handler.

7. `commands.py` includes the function `handle_command` which interprets and executes commands sent to the Swapper3D device such as connect, disconnect, send, and swap. This function communicates with the Swapper3D device via serial connection, logs the results of commands, and returns relevant HTTP responses.

In conclusion, this plugin provides a way to interact with a Swapper3D device directly from OctoPrint's interface. It allows for control of the device's operation, monitoring its status, and adjusting its settings.
