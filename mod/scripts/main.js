// this is some of the worst code i've written in my life

Log.info("Loaded mlogv32-utils.");

Blocks.worldProcessor.maxInstructionsPerTick = 1000000;

global.override.block(LogicBlock, {
    /**
     * @param {Table} table
     */
    buildConfiguration(table) {
        const buttons = table.table().get();
        this.super$buildConfiguration(buttons);

        if (isMlogv32Processor(this)) {
            buttons
                .button(Icon.download, Styles.cleari, () => {
                    Vars.platform.showFileChooser(true, "bin", (file) => {
                        try {
                            flashMlogv32Processor(this, file);
                        } catch (e) {
                            Log.err(e);
                            Vars.ui.hudfrag.showToast(
                                Icon.warning,
                                "Failed to flash processor RAM: " + e
                            );
                        }
                    });
                })
                .tooltip("Flash mlogv32 bin file")
                .size(40);
        }
    },
});

/**
 * @param {LogicBuild} processor
 * @returns {boolean}
 */
function isMlogv32Processor(processor) {
    return (
        processor.executor.optionalVar("MEMORY_X") != null &&
        processor.executor.optionalVar("MEMORY_Y") != null &&
        processor.executor.optionalVar("MEMORY_WIDTH") != null &&
        processor.executor.optionalVar("MEMORY_END") != null &&
        processor.executor.optionalVar("MEMORY_PROC_SIZE") != null
    );
}

/**
 * @param {LogicBuild} processor
 * @param {Fi} file
 */
function flashMlogv32Processor(processor, file) {
    const RAM_X = processor.executor.optionalVar("MEMORY_X").numval;
    const RAM_Y = processor.executor.optionalVar("MEMORY_Y").numval;
    const RAM_WIDTH = processor.executor.optionalVar("MEMORY_WIDTH").numval;
    const RAM_SIZE = processor.executor.optionalVar("MEMORY_END").numval;
    const RAM_PROC_SIZE = processor.executor.optionalVar("MEMORY_PROC_SIZE").numval;

    /** @type number[] */
    const data = file.readBytes();
    if (data.length % 4 != 0) {
        throw new Error("Invalid data alignment, length must be a multiple of 4 bytes!");
    } else if (data.length > RAM_SIZE) {
        throw new Error("Data too large!");
    }

    let ramIndex = 0;
    let varIndex = 1; // 0 is @counter

    /** @returns {LogicBuild} */
    function getRam() {
        const x = RAM_X + (ramIndex % RAM_WIDTH);
        const y = RAM_Y + Math.floor(ramIndex / RAM_WIDTH);

        const ram = Vars.world.build(x, y);
        if (ram == null || ram.executor.vars[1].name != "!!") {
            throw new Error("Tried to write to invalid RAM proc at " + x + "," + y);
        }

        return ram;
    }

    let ram = getRam();

    for (let i = 0; i < data.length; i += 4) {
        if (varIndex > RAM_PROC_SIZE) {
            ramIndex++;
            varIndex = 1;
            ram = getRam();
        }

        const value =
            ((data[i] & 0xff) << 24) |
            ((data[i + 1] & 0xff) << 16) |
            ((data[i + 2] & 0xff) << 8) |
            (data[i + 3] & 0xff);

        // i hate javascript
        ram.executor.vars[varIndex].setnum(value >>> 0);
        varIndex++;
    }

    Vars.ui.hudfrag.showToast(
        "Done! Loaded " +
            data.length +
            " bytes from " +
            file.name() +
            " into " +
            (ramIndex + 1) +
            " RAM procs."
    );
}
