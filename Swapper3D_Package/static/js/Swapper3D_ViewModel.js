// Octoprint plugin name: Swapper3D, File: Swapper3D_ViewModel.py, Author: BigBrain3D, License: AGPLv3
function Swapper3DViewModel(parameters) {
    var self = this;

    self.control = parameters[0];  // ControlViewModel instance

    self.onDataUpdaterPluginMessage = function(plugin, data) {
        if (plugin === "Swapper3D") {
            if (data.type === "log") {
                self.logToSwapper3D(data.message);
            } else if (data.type === "connectionState") {
                $("#connectionState").val(data.message);
            } else if (data.type === "currentlyLoadedInsert") {
                $("#currentlyLoadedInsert").val(data.message);
            } else if (data.type === "firmwareVersion") {
                $("#installedFirmwareVersion").val(data.message);
                self.sendCommandToSwapper3D("get latest firmware version");
            } else if (data.type === "latestFirmwareVersion") {
                $("#latestFirmwareVersion").val(data.message);
            }
        }
    };

    self.logToSwapper3D = function(message) {
        var existingContent = $("#Swapper3DLog").val();
        var newContent = existingContent + message + "\n";
        $("#Swapper3DLog").val(newContent);
        $("#Swapper3DLog").scrollTop($("#Swapper3DLog")[0].scrollHeight);
    };

    self.connectSwapper3D = function() {
        self.logToSwapper3D("Connect Swapper3D button was clicked");
        self.sendCommandToSwapper3D("connect");
    };

    self.disconnectSwapper3D = function() {
        self.logToSwapper3D("Disconnect Swapper3D button was clicked");
        self.sendCommandToSwapper3D("disconnect");
    };

    self.unloadInsert = function(event) {
        event.preventDefault();
        self.logToSwapper3D("Unload Insert button was clicked");
        self.sendCommandToSwapper3D("unload");
    };

	self.swapToInsert = function(event) {
		event.preventDefault();
		var selectedInsert = $("#insertDropdown").val();
		
		//subtract 1 from the selected insert before sending
		var adjustedInsert = parseInt(selectedInsert, 10) - 1; // use parseInt to ensure adjustInsert is an integer
		if (isNaN(adjustedInsert)) {
		   self.logToSwapper3D("Error: selected value not a number");
		   return;
		}
		self.logToSwapper3D("SwapToInsert button was clicked: " + adjustedInsert);
		self.sendCommandToSwapper3D("load_insert", adjustedInsert.toString());
	};

    self.boreAlignmentOn = function() {
        self.logToSwapper3D("Bore alignment on button was clicked");
        self.sendCommandToSwapper3D("borealignon");
    };

    self.boreAlignmentOff = function() {
        self.logToSwapper3D("Bore alignment off button was clicked");
        self.sendCommandToSwapper3D("borealignoff");
    };

    self.sendCommandToSwapper3D = function(command, insert_number = null) {
        var payload = {
            command: command
        };

        if (insert_number) {
            payload["insert_number"] = insert_number;
        }

        $.ajax({
            url: "/plugin/Swapper3D/command",
            type: "POST",
            dataType: "json",
            data: JSON.stringify(payload),
            contentType: "application/json; charset=utf-8",
            success: function(response) {
                self.logToSwapper3D(command.charAt(0).toUpperCase() + command.slice(1) + " command successful");
            },
            error: function(jqXHR) {
                self.logToSwapper3D(command.charAt(0).toUpperCase() + command.slice(1) + " command failed: " + jqXHR.responseText);
            }
        });
    };

    self.onStartupComplete = function() {
        $('#connectSwapper3D').click(self.connectSwapper3D);
        $('#disconnectSwapper3D').click(self.disconnectSwapper3D);
        $('#unloadInsertButton').click(self.unloadInsert);
        $('#swapToInsertButton').click(self.swapToInsert);
        $('#boreAlignmentOnButton').click(self.boreAlignmentOn);
        $('#boreAlignmentOffButton').click(self.boreAlignmentOff);
        $("#currentlyLoadedInsert").val("None");
    };
}

// Register the ViewModel
ADDITIONAL_VIEWMODELS.push([
    Swapper3DViewModel,
    ["controlViewModel"],
    ["#tab_plugin_Swapper3D"]
]);
