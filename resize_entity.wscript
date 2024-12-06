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


// constants ------------------------------------------------------------
// settings
const DEFAULT_CONFIG = {
    "verbose": false,
    "comment0": "verbose: True means more detailed logging.",
    "scaleFactor": 1.0,
    "comment1": "scaleFactor: The scale factor to resize the entity by.",
    "entityPath": "",
    "comment2": "entityPath: The path to the entity to resize. Make sure to escape the backslashes in the path by doubling them.",
    "overwriteVanilla": true,
    "comment3": "overwriteVanilla: Whether to overwrite the vanilla entity.",
    "customRootPath": "",
    "comment4": "customRootPath: The path to the custom root to use for the entity, only used if overwriteVanilla is false. Make sure to escape the backslashes in the path by doubling them.",
    "customPaths": {
        "rig": "\\rigs\\",
        "app": "\\appearances\\",
        "ent": "\\entities\\",
        "anims": "\\animations\\",
        "es": "\\fx\\es\\",
        "effect": "\\fx\\effects\\",
        "particle": "\\fx\\particles\\"
    },
    "comment5": "customPaths: The output paths for the resized resources (will be appended to the customRootPath), if overwriteVanilla is false. Escape the backslashes in the path by doubling them."
};

const config_path = "resize_entity_config.json"

let config = {};

// functions ------------------------------------------------------------

// general use utils
const utils = {
    // return bool or json object
    getConfig() {
        if (wkit.FileExistsInRaw(config_path)) {
            config = JSON.parse(wkit.LoadRawJsonFromProject(config_path, "json"));
            return true;
        } else {
            wkit.SaveToRaw(config_path, JSON.stringify(DEFAULT_CONFIG, null, 2));
            return false;
        }
    },
    // return bool
    validateConfig() {
        let valid = true;
        // validate the config
        if (config.scaleFactor <= 0) {
            Logger.Error('Scale factor must be greater than 0.');
            valid = false;
        }
        if (config.entityPath == '') {
            Logger.Error('Entity path is required.');
            valid = false;
        }
        if (!config.entityPath.endsWith('.ent')) {
            Logger.Error('Entity path must end with .ent');
            valid = false;
        }
        return valid;
    },
    // return bool or json object
    loadFileAsJson(path) {
        try {
            return JSON.parse(wkit.GetFile(path, OpenAs.Json));
        } catch (error) {
            Logger.Error('Error loading file as json: ' + error);
            return false;
        }
    }
}

// process file types
const processFiles = {
    // return bool
    entity() {
        // load the entity
        Logger.Info('Processing entity: ' + config["entityPath"]);
        let entity = utils.loadFileAsJson(config["entityPath"]);
        if (entity == false) {
            return;
        }
    
        // process the entities components and dependencies
        const [entity_success, entity_new] = processGeneric.appearance(entity);
        if (!entity_success) {
            Logger.Error("Failed to process entity components.");
            return false;
        }
        entity = entity_new;
    
        // process the linked appearance file if it exists
    
        // save the entity, implement later
    
        return true;
    }
}

// process generic -> functions that are used for multiple file types
const processGeneric = {
    
    // return bool, array of resolved dependencies
    // should work, but not tested
    repathDependencies(dependencies) {
        Logger.Info('Repathing dependencies...');
        try {
            const repathedDependencies = [];
            for (const dependency of dependencies) {
                if (dependency["DepotPath"]) {
                    const fileNameOnly = dependency["DepotPath"]["$value"].split("\\").pop();
                    const ext = fileNameOnly.substring(fileNameOnly.lastIndexOf('.'));
                    
                    if (ext in config["customPaths"]) {
                        const newPath = config["customRootPath"] + config["customPaths"][ext.substring(1)] + fileNameOnly;
                        dependency["DepotPath"]["$value"] = newPath;
                    }
                    repathedDependencies.push(dependency);
                } else {
                    Logger.Warn('No DepotPath found for dependency: ' + dependency);
                }
            }
            Logger.Success('Repathed dependencies successfully.');
            return [true, repathedDependencies];
        } catch (error) {
            Logger.Error('Error repathing dependencies: ' + error);
            return [false, []];
        }
    },
    // return bool, json object (same as input only with the changed components and resolved dependencies)
    // takes either an entire entity directly or an appearance from the appearances array in the app file
    appearance(appearance) {
        Logger.Info('Processing appearance...');
        try {
    
            // first process the components
            const components = appearance['Data']['RootChunk']['components'];
            const [comp_success, components_new] = processComponents.array(components);
            if (!comp_success) {
                Logger.Error("Failed to process components.");
                return [false, []];
            }
            appearance['Data']['RootChunk']['components'] = components_new;
    
            // then repath the dependencies
            const [dep_success, dependencies_new] = processGeneric.repathDependencies(appearance['Data']['RootChunk']['resolvedDependencies'], config);
            if (!dep_success) {
                Logger.Error("Failed to repath dependencies.");
                return [false, []];
            }
            appearance['Data']['RootChunk']['resolvedDependencies'] = dependencies_new;
            return [true, appearance];
        } catch (error) {
            Logger.Error('Error processing appearance: ' + error);
            return [false, []];
        }
    }

}

// process components
const processComponents = {
    // Process WorldPosition with FixedPoint values
    position(position, scaleFactor) {
        try {
            if (position['$type'] !== 'WorldPosition') {
                Logger.Error('Invalid position type: ' + position['$type']);
                return [false, position];
            }

            // Scale each coordinate's Bits value
            ['x', 'y', 'z'].forEach(coord => {
                if (position[coord] && position[coord]['$type'] === 'FixedPoint') {
                    position[coord]['Bits'] = Math.round(position[coord]['Bits'] * scaleFactor);
                }
            });

            return [true, position];
        } catch (error) {
            Logger.Error('Error processing position: ' + error);
            return [false, position];
        }
    },

    // Process the entire transform
    localTransform(transform, scaleFactor) {
        try {
            if (transform['$type'] !== 'WorldTransform') {
                Logger.Error('Invalid transform type: ' + transform['$type']);
                return [false, transform];
            }

            // Process Position if it exists
            if (transform['Position']) {
                const [success, newPosition] = this.position(transform['Position'], scaleFactor);
                if (!success) {
                    return [false, transform];
                }
                transform['Position'] = newPosition;
            }

            return [true, transform];
        } catch (error) {
            return [false, transform];
        }
    },
    entSlotComponent(component) {
        try {
            for (const slot of component["slots"]) {
                slot["relativePosition"]["X"] *= config["scaleFactor"];
                slot["relativePosition"]["Y"] *= config["scaleFactor"];
                slot["relativePosition"]["Z"] *= config["scaleFactor"];
            }
            return [true, component];
        } catch (error) {
            Logger.Error('Error processing entSlotComponent: ' + error);
            return [false, component];
        }
    },
    entMeshComponent(component) {
        try {
            component["visualScale"]["X"] *= config["scaleFactor"];
            component["visualScale"]["Y"] *= config["scaleFactor"];
            component["visualScale"]["Z"] *= config["scaleFactor"];
            return [true, component];
        } catch (error) {
            Logger.Error('Error processing entMeshComponent: ' + error);
            return [false, component];
        }
    },
    entAnimatedComponent(component) {
        return [true, component];
    },
    entEffectSpawnerComponent(component) {
        return [true, component];
    },
    entLightChannelComponent(component) {
        return [true, component];
    },
    cerberusComponent(component) {
        return [true, component];
    },
    
    // return bool, array of components
    // takes an array of components and resizes them, returns true if successful
    // is the entry point for processing components
    array(components) {
        const processedComponents = [];
        try {
            for (const component of components) {
                // try to adjust the local Transform on component level
                try {
                    const [success, newTransform] = processComponents.localTransform(component['localTransform'], config["scaleFactor"]);
                    if (!success) {
                        if (config["verbose"]) {
                            Logger.Warning('Failed to process localTransform for component: ' + component['$type']);
                        }
                    } else {
                        component['localTransform'] = newTransform;
                    }
                } catch (error) {
                    Logger.Warning('No localTransform found for component: ' + component['$type']);
                }

                // get the action type for the component
                const actionTypes = {
                    "entSlotComponent": () => processComponents.entSlotComponent(component),
                    "entMeshComponent": () => processComponents.entMeshComponent(component),
                    "entPhysicalMeshComponent": () => processComponents.entMeshComponent(component),
                    "entAnimatedComponent": () => processComponents.entAnimatedComponent(component),
                    "entEffectSpawnerComponent": () => processComponents.entEffectSpawnerComponent(component),
                    "entLightChannelComponent": () => processComponents.entLightChannelComponent(component),
                    "cerberusComponent": () => processComponents.cerberusComponent(component), // special case for cerberus, linking to an .es file
                }

                // If component type exists in actionTypes, process it, otherwise just pass it through
                if (component['$type'] in actionTypes) {
                    const [success, component_new] = actionTypes[component['$type']](component);
                    if (!success) {
                        Logger.Error("Failed to process component: " + component['$type']);
                        return [false, []];
                    }
                    processedComponents.push(component_new);
                } else {
                    if (config["verbose"]) {
                        Logger.Info("Skipping generic component type: " + component['$type']);
                    }
                    processedComponents.push(component);
                }
            }
        } catch (error) {
            Logger.Error('Error processing components: ' + error);
            return [false, []];
        }
        return [true, processedComponents];
    }
}

// return void
function main() {
    Logger.Info('Starting resize entity script...');
    // get config or create and exit early if no config existed at the start
    if (!utils.getConfig()) {
        Logger.Error('No config file found, created default config in raw. Please fill it with the required values and run the script again.');
        return;
    }
    Logger.Success('Config loaded successfully.');

    if (!utils.validateConfig()) {
        Logger.Error('Config is invalid, please fix the config and run the script again.');
        return;
    }

    Logger.Info('Config is valid, starting resize process...');

    if (!processFiles.entity()) {
        Logger.Error('Error processing entity, please check the console for more information.');
        return;
    }
}

main();

