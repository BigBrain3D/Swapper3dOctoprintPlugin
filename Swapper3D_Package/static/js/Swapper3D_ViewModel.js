//Octoprint plugin name: Swapper3D, File: Swapper3D_ViewModel.js, Author: BigBrain3D, License: AGPLv3 

function Swapper3DViewModel(parameters) {
    var self = this;

    self.control = parameters[0];  // ControlViewModel instance

    self.onDataUpdaterPluginMessage = function(plugin, data) {
        if (plugin === "Swapper3D") {
            if (data.type === "log") {
                var logEntry = data.message;
                self.updateLog(logEntry);
            } else if (data.type === "connectionState") {
                $("#connectionState").val(data.message);
            }
        }
    };

    self.connectSwapper3D = function() {
        console.log("Handshake Swapper3D button was clicked");
        self.updateLog("Handshake Swapper3D button was clicked");

        // Only attempt to connect if we're currently disconnected
        if ($("#connectionState").val() !== "Connected") {
            $.ajax({
                url: "/plugin/Swapper3D/command",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    command: "connect"
                }),
                contentType: "application/json; charset=utf-8",
                success: function(response) {
                    console.log("Handshake started");
                },
                error: function(jqXHR) {
                    console.log("Handshake failed: " + jqXHR.responseText);
                }
            });
        } else {
            self.updateLog("Attempted to connect while already connected.");
        }
    };

    self.disconnectSwapper3D = function() {
        console.log("Disconnect Swapper3D button was clicked");
        self.updateLog("Disconnect Swapper3D button was clicked");

        $.ajax({
            url: "/plugin/Swapper3D/command",
            type: "POST",
            dataType: "json",
            data: JSON.stringify({
                command: "disconnect"
            }),
            contentType: "application/json; charset=utf-8",
            success: function(response) {
                console.log("Disconnect started");
            },
            error: function(jqXHR) {
                console.log("Disconnect failed: " + jqXHR.responseText);
            }
        });
    };

    self.unloadInsert = function(event) {
        event.preventDefault();
        console.log("Unload Insert button was clicked");
        $("#currentlyLoadedInsert").val("None");
        self.updateLog("Unload Insert button was clicked. Current Insert set to None.");
    };

    self.swapToInsert = function(event) {
        event.preventDefault();
        console.log("SwapToInsert button was clicked");
        var selectedInsert = $("#insertDropdown").val();
        $("#currentlyLoadedInsert").val(selectedInsert);
        self.updateLog("SwapToInsert button was clicked. Current Insert set to " + selectedInsert + ".");
    };

    self.updateLog = function(message) {
        var existingContent = $("#Swapper3DLog").val();
        var newContent = existingContent + message + "\n";
        $("#Swapper3DLog").val(newContent);
        // Scroll to the bottom
        $("#Swapper3DLog").scrollTop($("#Swapper3DLog")[0].scrollHeight);
    }

    self.onStartupComplete = function() {
        $('#connectSwapper3D').click(self.connectSwapper3D);
        $('#disconnectSwapper3D').click(self.disconnectSwapper3D);
        $('#unloadInsertButton').click(self.unloadInsert);
        $('#swapToInsertButton').click(self.swapToInsert);
        $("#connectionState").val("Disconnected");  // initial state is Disconnected
        $("#currentlyLoadedInsert").val("None");
        // initial state is None
    };
}

// Register the ViewModel
ADDITIONAL_VIEWMODELS.push([
    Swapper3DViewModel,
    ["controlViewModel"],  // ControlViewModel instance is required
    ["#tab_plugin_Swapper3D"]
]);
