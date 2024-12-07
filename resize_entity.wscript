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
        "effect": "\\fx\\effects\\"
    },
    "comment5": "customPaths: The output paths for the resized resources (will be appended to the customRootPath), if overwriteVanilla is false. Escape the backslashes in the path by doubling them.",
    "ChangeLODMode": false,
    "comment6": "ChangeLODMode: Whether to set all mesh components to AlwaysVisible. (Only needd if you scale the entity up significantly)"
};

const config_path = "resize_entity_config.json"

let config = {};

let savedFileData = [];
let savedFilePaths = [];

// functions ------------------------------------------------------------

// general use utils
const utils = {
    /**
     * @returns {boolean}
     */
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
    /**
     * @returns {boolean}
     */
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
    /**
     * @returns {boolean | json}
     */
    loadFileAsJson(path) {
        try {
            const file = wkit.GetFile(path, OpenAs.Json);
            if (file == null) {
                Logger.Error('Failed to load file: ' + path);
                return false;
            }
            return JSON.parse(file);
        } catch (error) {
            Logger.Error('Error loading file as json: ' + error);
            return false;
        }
    },
    /**
     * @returns {string | boolean}
     */
    repathToSave(path) {
        if (config["verbose"]) {
            Logger.Info("Repathing path: " + path);
        }
        if (config["overwriteVanilla"]) {
            if (config["verbose"]) {
                Logger.Info("Overwriting vanilla, skipping repathing.");
            }
            return path;
        }
        try {
            const fileNameOnly = path.split("\\").pop();
            const ext = fileNameOnly.split(".")[1];

            return config["customRootPath"] + config["customPaths"][ext] + fileNameOnly;
        } catch (error) {
            Logger.Error('Error repathing before saving: ' + error);
            return false;
        }
    },
    /**
     * @returns {boolean}
     */
    saveJsonAsGameFile(path, data, skipRepath = false) {
        let savePath = path;
        let dataToSave = data;
        if (!skipRepath) {
            Logger.Info('Repathing path: ' + path);
            savePath = utils.repathToSave(path);
            if (savePath == false) {
                return false;
            }
            Logger.Info('Repathed path: ' + savePath);
        } else {
            savePath = path;
        }

        let cr2wContent = null;
        try {
            if (typeof dataToSave == "string") {
                cr2wContent = wkit.JsonToCR2W(dataToSave);
            } else {
                cr2wContent = wkit.JsonToCR2W(JSON.stringify(dataToSave, null, 2));
            }
        } catch (err) {
            Logger.Error(`Couldn't parse active file content to cr2w:`);
            Logger.Error(err);
            return false;
        }
    
        try {
            wkit.SaveToProject(savePath, cr2wContent); 
        } catch (err) {
            Logger.Error(`Couldn't save ${savePath}:`);
            Logger.Error(err);
            return false;
        }
        return true;
    },
    /**
     * @returns {boolean}
     */
    addFileToSaveBuffer(path, data) {
        Logger.Info("Adding file to save buffer: " + path);
        savedFilePaths.push(path);
        savedFileData.push(JSON.stringify(data, null, 2));
        return true;
    },
    /**
     * @returns {boolean}
     */
    saveFiles() {
        for (let i = 0; i < savedFilePaths.length; i++) {
            const filePath = savedFilePaths[i];
            const fileData = savedFileData[i];
            Logger.Info('Saving file: ' + filePath);
            utils.saveJsonAsGameFile(filePath, fileData);
        }
        return true;
    }
}

// process file types
const processFiles = {
    /**
     * @returns {boolean}
     */
    entity() {
        // load the entity
        Logger.Info('Processing entity: ' + config["entityPath"]);
        let entity = utils.loadFileAsJson(config["entityPath"]);
        if (entity == false) {
            return false;
        }
    
        // process the entities components and dependencies
        const [entity_success, entity_new] = processGeneric.appearance(entity);
        if (!entity_success) {
            Logger.Error("Failed to process entity components.");
            return false;
        }
        entity = entity_new;
        try {
            let appearancefiles = [];
            const appearances = entity["Data"]["RootChunk"]["appearances"];
            for (let index = 0; index < appearances.length; index++) {
                const appearance = appearances[index];
                appearancefiles.push(appearance["appearanceResource"]["DepotPath"]["$value"]);
                appearances[index]["appearanceResource"]["DepotPath"]["$value"] = utils.repathToSave(appearance["appearanceResource"]["DepotPath"]["$value"]);
            }
            const uniqueAppearanceFiles = [...new Set(appearancefiles)];
            for (const appearanceFile of uniqueAppearanceFiles) {
                processFiles.appearance(appearanceFile);
            }
        } catch (error) {
            Logger.Error('Error processing appearances: ' + error);
            return false;
        }
    
        // save the entity
        if (!utils.addFileToSaveBuffer(config["entityPath"], entity)) {
            Logger.Error("Failed to save entity.");
            return false;
        }
        Logger.Success("Entity added to save buffer.");
        return true;
    },
    /**
     * @returns {boolean}
     */
    rig(rigFilepath) {
        Logger.Info('Processing rig: ' + rigFilepath);
        let rig = utils.loadFileAsJson(rigFilepath);
        if (rig == false) {
            return false;
        }
        try {
            for (const bone of rig['Data']['RootChunk']['boneTransforms']) {
                // Scale the Scale values
                bone['Scale']['X'] *= config["scaleFactor"];
                bone['Scale']['Y'] *= config["scaleFactor"];
                bone['Scale']['Z'] *= config["scaleFactor"];
                
                // Scale the Position values
                bone['Translation']['X'] *= config["scaleFactor"];
                bone['Translation']['Y'] *= config["scaleFactor"];
                bone['Translation']['Z'] *= config["scaleFactor"];
            }
        } catch (error) {
            Logger.Error('Error processing rig (' + rigFilepath + '): ' + error);
            return false;
        }
        if (!utils.addFileToSaveBuffer(rigFilepath, rig)) {
            Logger.Error('Failed to save rig.');
            return false;
        }
        Logger.Success('Rig added to save buffer.');
        return true;
    },
    /**
     * @returns {boolean}
     */
    anims(animFilepath) {
        // there is no need to process the rig here as it will have been done as part of the component processing, so we just repath here
        Logger.Info('Processing anims: ' + animFilepath);
        const anim = utils.loadFileAsJson(animFilepath);
        if (anim == false) {
            return false;
        }
        const rigFilepath = utils.repathToSave(anim["Data"]["RootChunk"]["rig"]["DepotPath"]["$value"]);
        if (rigFilepath == false) {
            return false;
        }
        anim["Data"]["RootChunk"]["rig"]["DepotPath"]["$value"] = rigFilepath;
        if (!utils.addFileToSaveBuffer(animFilepath, anim)) {
            Logger.Error('Failed to save anims.');
            return false;
        }
        Logger.Success('Anims added to save buffer.');
        return true;
    },
    /**
     * @returns {boolean}
     */
    effect(effectFilepath) {
        Logger.Info('Processing effect: ' + effectFilepath);
        if (!effectFilepath.endsWith(".effect")) {
            Logger.Info('Effect is not an effect file, skipping.');
            return true;
        }
        let effect = utils.loadFileAsJson(effectFilepath);
        if (effect == false) {
            Logger.Warning('Failed to load effect.');
            return true;
        }
        
        for (let effectEvent of effect["Data"]["RootChunk"]["events"]) {
            
            if (effectEvent["Data"]["$type"] == "effectTrackItemParticles") {
                if (effectEvent["Data"]["size"]["evaluator"]["Data"]["value"] == undefined) {
                    Logger.Warning('No size found for particle effect.');
                    continue
                }
                try {
                    effectEvent["Data"]["size"]["evaluator"]["Data"]["value"] *= config["scaleFactor"];
                } catch (error) {
                    Logger.Error('Error scaling particle size: ' + error);
                    Logger.Error('Event structure: ' + JSON.stringify(effectEvent["Data"], null, 2));
                    return false;
                }
            }
        }

        if (!utils.addFileToSaveBuffer(effectFilepath, effect)) {
            Logger.Error('Failed to save effect to buffer.');
            return false;
        }
        Logger.Success('Effect added to save buffer.');
        return true;
    },
    /**
     * @returns {boolean}
     */
    appearance(appearanceFilepath) {
        Logger.Info('Processing appearance: ' + appearanceFilepath);
        let appearance = utils.loadFileAsJson(appearanceFilepath);
        if (appearance == false) {
            Logger.Warning('Failed to load appearance.');
            return true;
        }

        // Create a direct reference to the appearances array
        const appearances = appearance["Data"]["RootChunk"]["appearances"];
        
        // Process each appearance in the array
        for (let i = 0; i < appearances.length; i++) {
            const currentAppearance = appearances[i];
            const [success, newAppearance] = processGeneric.appearance(currentAppearance, false);
            if (!success) {
                Logger.Error('Failed to process appearance at index ' + i);
                return false;
            }
            appearances[i] = newAppearance;
        }

        if (!utils.addFileToSaveBuffer(appearanceFilepath, appearance)) {
            Logger.Error('Failed to save appearance to buffer.');
            return false;
        }
        Logger.Success('Appearance added to save buffer.');
        return true;
    }
}

// process generic -> functions that are used for multiple file types
const processGeneric = {
    
    /**
     * @returns {boolean | array}
     */
    repathDependencies(dependencies) {
        if (config["overwriteVanilla"]) {
            Logger.Info('Overwriting vanilla, skipping repathing.');
            return [true, dependencies];
        }
        Logger.Info('Repathing dependencies...');
        try {
            const repathedDependencies = [];
            for (const dependency of dependencies) {
                if (dependency["DepotPath"]) {
                    if (!(dependency["DepotPath"]["$value"].split("\\").pop().split(".").pop() in config["customPaths"])) {
                        repathedDependencies.push(dependency);
                        continue;
                    }
                    const newPath = utils.repathToSave(dependency["DepotPath"]["$value"]);
                    if (newPath == false) {
                        Logger.Error('Failed to repath dependency: ' + dependency);
                        return [false, []];
                    }
                    dependency["DepotPath"]["$value"] = newPath;
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
    /**
     * @returns {boolean | json}
     */
    appearance(appearance, isEntity = true) {
        Logger.Info('Processing appearance...');
        try {
    
            // first process the components
            let components;
            if (isEntity) {
                components = appearance['Data']['RootChunk']['components'];
            } else {
                components = appearance['Data']['components'];
            }
            const [comp_success, components_new] = processComponents.array(components, appearance);
            if (!comp_success) {
                Logger.Error("Failed to process components.");
                return [false, []];
            }
            if (isEntity) {
                appearance['Data']['RootChunk']['components'] = components_new;
            } else {
                appearance['Data']['components'] = components_new;
            }
    
            // then repath the dependencies
            Logger.Info('Repathing dependencies...');
            let dep_success, dependencies_new;
            if (isEntity) {
                [dep_success, dependencies_new] = processGeneric.repathDependencies(appearance['Data']['RootChunk']['resolvedDependencies']);
            } else {
                [dep_success, dependencies_new] = processGeneric.repathDependencies(appearance['Data']['resolvedDependencies']);
            }
            if (!dep_success) {
                Logger.Error("Failed to repath dependencies.");
                return [false, []];
            }
            Logger.Success('Generated new dependencies successfully.');
            if (isEntity) {
                appearance['Data']['RootChunk']['resolvedDependencies'] = dependencies_new;
            } else {
                appearance['Data']['resolvedDependencies'] = dependencies_new;
            }
            Logger.Success('Saved new dependencies successfully.');
            return [true, appearance];
        } catch (error) {
            Logger.Error('Error processing appearance: ' + error);
            return [false, []];
        }
    }

}

// process components
const processComponents = {
    /**
     * @returns {boolean | integer | json}
     */
    getChunkbyId(id, rawJson) {
        const chunks = rawJson["Data"]["RootChunk"]["compiledData"]["Data"]["Chunks"];
        let index = 0;
        for (const chunk of chunks) {
            if (chunk["id"] == id) {
                return [true, index, chunk];
            }
            index++;
        }
        return [false, -1, {}];
    },
    /**
     * @returns {boolean | json}
     */
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

    /**
     * @returns {boolean | json}
     */
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
    /**
     * @returns {boolean | json}
     */
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
            if (config["ChangeLODMode"]) {
                component["LODMode"] = "AlwaysVisible";
            }
            return [true, component];
        } catch (error) {
            Logger.Error('Error processing entMeshComponent: ' + error);
            return [false, component];
        }
    },
    entAnimatedComponent(component) {
        // get rig file
        try {
            const rigFilepath = component["rig"]["DepotPath"]["$value"];
            processFiles.rig(rigFilepath);
            const newRigFilepath = utils.repathToSave(rigFilepath);
            if (newRigFilepath == false) {
                return [false, component];
            }
            component["rig"]["DepotPath"]["$value"] = newRigFilepath;
        } catch (error) {
            if (config["verbose"]) {
                Logger.Warning('No rig file found for entAnimatedComponent');
            }
        }

        // get animation files
        try {
            const animsArray = component["animations"]["gameplay"];
            for (const anim of animsArray) {
                if (anim["$type"] != "animAnimSetupEntry") {
                    continue;
                }
                const animFilepath = anim["animSet"]["DepotPath"]["$value"];
                processFiles.anims(animFilepath);
                const newAnimFilepath = utils.repathToSave(animFilepath);
                if (newAnimFilepath == false) {
                    return [false, component];
                }
                anim["animSet"]["DepotPath"]["$value"] = newAnimFilepath;
            }
        } catch (error) {
            if (config["verbose"]) {
                Logger.Warning('No anims file found for entAnimatedComponent');
            }
        }

        return [true, component];
    },
    entEffectSpawnerComponent(component, rawJson) {
        Logger.Info('Processing entEffectSpawnerComponent...');
        try {
            const id = component["id"];
            const [success, index, chunk] = processComponents.getChunkbyId(id, rawJson);
            if (!success) {
                Logger.Error('Failed to get chunk by id for entEffectSpawnerComponent');
                return [false, component];
            }
            Logger.Info("Got Chunk: " + Object.keys(chunk));
            for (const effect of chunk["effectDescs"]) {
                Logger.Info("Effect: " + Object.keys(effect["Data"]));
                processFiles.effect(effect["Data"]["effect"]["DepotPath"]["$value"]);
                const newEffectFilepath = utils.repathToSave(effect["Data"]["effect"]["DepotPath"]["$value"]);
                if (newEffectFilepath == false) {
                    return [false, component];
                }
                effect["Data"]["effect"]["DepotPath"]["$value"] = newEffectFilepath;
                for (const effectPos of effect["Data"]["compiledEffectInfo"]["relativePositions"]) {
                    effectPos["X"] *= config["scaleFactor"];
                    effectPos["Y"] *= config["scaleFactor"];
                    effectPos["Z"] *= config["scaleFactor"];
                }
            }
            Logger.Info("Saving new chunk...");
            rawJson["Data"]["RootChunk"]["compiledData"]["Data"]["Chunks"][index] = chunk;
            Logger.Success("Saved new chunk successfully.");

            return [true, component];
        } catch (error) {
            Logger.Error('Error processing entEffectSpawnerComponent: ' + error);
            return [false, component];
        }
    },
    entLightChannelComponent(component, rawJson) {
        // need to go from `HandleRefId` to array of vertices
        const [success, index, chunk] = processComponents.getChunkbyId(component["id"], rawJson);
        if (!success) {
            Logger.Error('Failed to get chunk by id for entLightChannelComponent');
            return [false, component];
        }
        try {
            const vertices = chunk["shape"]["Data"]["vertices"];
            for (const vertex of vertices) {
                vertex["X"] *= config["scaleFactor"];
                vertex["Y"] *= config["scaleFactor"];
                vertex["Z"] *= config["scaleFactor"];
            }
            chunk["shape"]["Data"]["vertices"] = vertices;
            rawJson["Data"]["RootChunk"]["compiledData"]["Data"]["Chunks"][index] = chunk;
        } catch (error) {
            Logger.Error('Error processing entLightChannelComponent: ' + error);
            return [false, component];
        }
        return [true, component];
    },
    cerberusComponent(component) {
        // get the es file 
        return [true, component];
    },
    
    /**
     * @returns {boolean | array}
     */
    array(components, rawJson) {
        Logger.Info('Processing components...');
        Logger.Info("Components: " + components.length);
        let index = 0;
        const processedComponents = [];
        try {
            for (const component of components) {
                Logger.Info("Component " + index + ": " + component['$type']);
                index++;
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
                    "entEffectSpawnerComponent": () => processComponents.entEffectSpawnerComponent(component, rawJson),
                    "entLightChannelComponent": () => processComponents.entLightChannelComponent(component, rawJson),
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

/**
 * @returns {void}
 */
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
    // save all files if process was successful
    if (!utils.saveFiles()) {
        Logger.Error('Error saving files, please check the console for more information.');
        return;
    }
    Logger.Success('Resize process completed successfully.');
}

main();

