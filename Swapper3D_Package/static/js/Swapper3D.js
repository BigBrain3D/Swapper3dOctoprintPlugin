/*
 * View model for Swapper3D
 *
 * Author: BigBrain3D
 * License: AGPLv3
 */
$(function() {
    function Swapper3DViewModel(parameters) {
        var self = this;

        self.settings = parameters[0];

        self.connectSwapper3D = function() {
            $.ajax({
                url: API_BASEURL + "plugin/swapper3d",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    command: "connect",
                    port: self.settings.settings.plugins.swapper3d.serialPort(),
                    baudrate: self.settings.settings.plugins.swapper3d.baudrate()
                }),
                contentType: "application/json; charset=UTF-8"
            }).done(function() {
                new PNotify({title: "Swapper3D", text: "Connected successfully!", type: "success"});
            }).fail(function() {
                new PNotify({title: "Swapper3D", text: "Failed to connect.", type: "error"});
            });
        };
    }

    ADDITIONAL_VIEWMODELS.push([
        Swapper3DViewModel,
        ["settingsViewModel"],
        ["#tab_plugin_swapper3d"]
    ]);
});


