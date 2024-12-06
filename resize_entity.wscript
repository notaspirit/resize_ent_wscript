// @author spirit
// @version 1.0
// @description
// This script resizes the given entity, including all components, effects, particles, lights, appearnaces etc.
// @usage
// Run the script to generate config file
// fill the config file with the required values
// run the script again to resize the entity

// imports
import * as Logger from 'Logger.wscript';
import * as TypeHelper from 'TypeHelper.wscript';

// settings
const DEFAULT_CONFIG = {
    scaleFactor: 1.0,
    comment1: "scaleFactor: The scale factor to resize the entity by.",
    entityPath: '',
    comment2: "entityPath: The path to the entity to resize.",
    overwriteVanilla: true,
    comment3: "overwriteVanilla: Whether to overwrite the vanilla entity.",
    customRootPath: '',
    comment4: "customRootPath: The path to the custom root to use for the entity, only used if overwriteVanilla is false."
};

const config_path = "resize_entity_config.json"

// gets the config file, creates it if it doesn't exist
function getConfig() {
    if (wkit.FileExistsInRaw(config_path)) {
        return JSON.parse(wkit.LoadRawJsonFromProject(config_path, "json"));
    } else {
        wkit.SaveToRaw(config_path, JSON.stringify(DEFAULT_CONFIG, null, 2));
        return false;
    }
}


// functions
function main() {
    Logger.Info('Starting resize entity script...');
    // get config or create and exit early if no config existed at the start
    let config = getConfig();
    if (config == false) {
        Logger.Error('No config file found, created default config. Please fill it with the required values and run the script again.');
        return;
    }
    Logger.Info('Config loaded successfully.');

}

main();

