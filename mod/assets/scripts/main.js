// this is some of the worst code i've written in my life

Blocks.worldProcessor.maxInstructionsPerTick = 1000000;

/** @type ClassLoader */
const loader = Vars.mods.getMod("mlogv32-utils").loader;
const ProcessorAccess = loader.loadClass("gay.object.mlogv32.ProcessorAccess");
const ProcessorAccess_Companion = ProcessorAccess.getField("Companion").get(null);

let serverAddress = "localhost";
let serverPort = 5000;

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

            buttons
                .button(Icon.host, Styles.clearTogglei, () => {
                    if (processor.isServerRunning()) {
                        processor.stopServer();
                        Vars.ui.hudfrag.showToast("Stopped socket server.");
                    } else {
                        const dialog = new BaseDialog("Server address");
                        dialog.addCloseButton();
                        dialog.cont
                            .field(serverAddress, (address) => {
                                serverAddress = address;
                            })
                            .tooltip("Address");
                        dialog.cont.row();
                        dialog.cont
                            .field(
                                serverPort.toString(),
                                TextField.TextFieldFilter.digitsOnly,
                                (portStr) => {
                                    const port = parseInt(portStr);
                                    if (!isNaN(port)) {
                                        serverPort = port;
                                    }
                                }
                            )
                            .tooltip("Port");
                        dialog.cont.row();
                        dialog.cont
                            .button("Confirm", Styles.defaultt, () => {
                                dialog.hide();
                                processor.startServer(serverAddress, serverPort);
                                Vars.ui.hudfrag.showToast(
                                    "Started socket server at " +
                                        serverAddress +
                                        ":" +
                                        serverPort +
                                        "."
                                );
                            })
                            .width(100);
                        dialog.show();
                    }
                })
                .tooltip("Start/stop mlogv32 socket server")
                .checked(processor.isServerRunning())
                .size(40);
        }
    },
});

let activeProcessors = [];

global.mlogv32 = {
    loadSchematic: (/** @type {string} */ arg) => {
        const [path, xRaw, yRaw, cpuXOffsetRaw, cpuYOffsetRaw, address, portRaw] = arg.split(" ");
        const x = parseFloat(xRaw);
        const y = parseFloat(yRaw);
        const cpuXOffset = parseFloat(cpuXOffsetRaw);
        const cpuYOffset = parseFloat(cpuYOffsetRaw);
        const port = parseInt(portRaw);
        if (
            !path.length ||
            isNaN(x) ||
            isNaN(y) ||
            isNaN(cpuXOffset) ||
            isNaN(cpuYOffset) ||
            isNaN(port) ||
            port < 0 ||
            port > 65535
        ) {
            Log.err("Invalid arguments.");
            return;
        }

        /** @type {Fi} */
        let file;
        if (path[0] == "/") {
            file = Core.files.absolute(path);
        } else {
            file = Core.files.local(path);
        }

        Log.info("Loading schematic: " + file);
        const schem = Schematics.read(file);

        Log.info("Placing schematic.");
        Schematics.place(
            schem,
            x + schem.width / 2,
            y + schem.height / 2,
            Vars.state.rules.defaultTeam,
            true
        );

        const cpuX = x + cpuXOffset;
        const cpuY = cpuYOffset >= 0 ? y + cpuYOffset : y + schem.height + cpuYOffset;
        Log.info("CPU position: " + cpuX + "," + cpuY);

        const build = Vars.world.build(cpuX, cpuY);
        if (build == null) {
            Log.err("CPU not found.");
            return;
        }

        Log.info("Waiting for CPU to initialize...");

        Time.runTask(60, () => {
            const processor = ProcessorAccess_Companion.of(build);
            if (processor == null) {
                Log.err("Invalid CPU: " + build);
                return;
            }

            processor.startServer(address, port);
            activeProcessors.push(processor);
        });
    },

    stopAll: () => {
        activeProcessors.forEach((processor) => processor.stopServer());
        Log.info(
            "Stopped " +
                activeProcessors.length +
                " processor" +
                (activeProcessors.length === 1 ? "" : "s") +
                "."
        );
        activeProcessors = [];
    },
};

Log.info("Loaded mlogv32-utils scripts.");
