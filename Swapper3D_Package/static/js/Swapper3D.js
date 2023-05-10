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

        // Your frontend logic goes here
    }

    // This is how your plugin gets registered with the application
    ADDITIONAL_VIEWMODELS.push([
        Swapper3DViewModel,
        ["settingsViewModel"],
        ["#tab_plugin_swapper3d"]
    ]);
});

