// this is some of the worst code i've written in my life

Blocks.worldProcessor.maxInstructionsPerTick = 1000000;

/** @type ClassLoader */
const loader = Vars.mods.getMod("mlogv32-utils").loader;
const ProcessorAccess = loader.loadClass("gay.object.mlogv32.ProcessorAccess");
const ProcessorAccess_Companion = ProcessorAccess.getField("Companion").get(null);

global.override.block(LogicBlock, {
    /**
     * @param {Table} table
     */
    buildConfiguration(table) {
        /** @type Table */
        const buttons = table.table().get();
        this.super$buildConfiguration(buttons);

        const processor = ProcessorAccess_Companion.of(this);
        if (processor != null) {
            buttons
                .button(Icon.download, Styles.cleari, () => {
                    Vars.platform.showFileChooser(true, "bin", (file) => {
                        try {
                            const bytes = processor.flashRom(file);
                            const message =
                                "Flashed " + bytes + " bytes from " + file.name() + " to ROM.";
                            Log.info(message);
                            Vars.ui.hudfrag.showToast("Done! " + message);
                        } catch (e) {
                            Log.err(e);
                            Vars.ui.hudfrag.showToast(Icon.warning, "Failed to flash ROM: " + e);
                        }
                    });
                })
                .tooltip("Flash mlogv32 ROM")
                .size(40);

            buttons
                .button(Icon.upload, Styles.cleari, () => {
                    Vars.platform.showFileChooser(false, "bin", (file) => {
                        try {
                            const bytes = processor.dumpRam(file);
                            const message =
                                "Dumped " + bytes + " bytes from RAM to " + file.name() + ".";
                            Log.info(message);
                            Vars.ui.hudfrag.showToast("Done! " + message);
                        } catch (e) {
                            Log.err(e);
                            Vars.ui.hudfrag.showToast(Icon.warning, "Failed to dump RAM: " + e);
                        }
                    });
                })
                .tooltip("Dump mlogv32 RAM")
                .size(40);
        }
    },
});

Log.info("Loaded mlogv32-utils scripts.");
