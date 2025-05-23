// this is some of the worst code i've written in my life

Log.info("Loaded mlogv32-utils.");

Blocks.worldProcessor.maxInstructionsPerTick = 1000000;

global.override.block(LogicBlock, {
    /**
     * @param {Table} table
     */
    buildConfiguration(table) {
        /** @type Table */
        const buttons = table.table().get();
        this.super$buildConfiguration(buttons);

        const memory = Mlogv32Memory_of(this);
        if (memory != null) {
            buttons
                .button(Icon.download, Styles.cleari, () => {
                    Vars.platform.showFileChooser(true, "bin", (file) => {
                        memory("flash")(
                            file,
                            (progress, total) => {
                                Vars.ui.hudfrag.setHudText(
                                    "Progress: " +
                                        progress +
                                        "/" +
                                        total +
                                        " (" +
                                        Math.floor((100 * progress) / total) +
                                        "%)"
                                );
                            },
                            (bytes) => {
                                Vars.ui.hudfrag.toggleHudText(false);
                                const message =
                                    "Loaded " + bytes + " bytes from " + file.name() + ".";
                                Log.info(message);
                                Vars.ui.hudfrag.showToast("Done! " + message);
                            },
                            (e) => {
                                Log.err(e);
                                Vars.ui.hudfrag.toggleHudText(false);
                                Vars.ui.hudfrag.showToast(
                                    Icon.warning,
                                    "Failed to flash processor RAM: " + e
                                );
                            }
                        );
                    });
                })
                .tooltip("Flash mlogv32 bin file")
                .size(40);

            buttons
                .button(Icon.upload, Styles.cleari, () => {
                    Vars.platform.showFileChooser(false, "bin", (file) => {
                        memory("dump")(
                            file,
                            (progress, total) => {
                                Vars.ui.hudfrag.setHudText(
                                    "Progress: " +
                                        progress +
                                        "/" +
                                        total +
                                        " (" +
                                        Math.floor((100 * progress) / total) +
                                        "%)"
                                );
                            },
                            (bytes) => {
                                Vars.ui.hudfrag.toggleHudText(false);
                                const message =
                                    "Dumped " + bytes + " bytes to " + file.name() + ".";
                                Log.info(message);
                                Vars.ui.hudfrag.showToast("Done! " + message);
                            },
                            (e) => {
                                Log.err(e);
                                Vars.ui.hudfrag.toggleHudText(false);
                                Vars.ui.hudfrag.showToast(
                                    Icon.warning,
                                    "Failed to dump processor RAM: " + e
                                );
                            }
                        );
                    });
                })
                .tooltip("Dump mlogv32 memory")
                .size(40);
        }
    },
});

/**
 *
 * @param {number} memoryX
 * @param {number} memoryY
 * @param {number} memoryWidth
 * @param {number} memoryLengthBytes
 * @param {number} memoryProcLengthVars
 * @returns {Mlogv32Memory}
 */
const Mlogv32Memory_new = (
    memoryX,
    memoryY,
    memoryWidth,
    memoryLengthBytes,
    memoryProcLengthVars
) => {
    /**
     * @param {number} address
     * @returns {LogicBuild}
     */
    function getProcessor(address) {
        if (address >= memoryLengthBytes) {
            throw new Error("Tried to read invalid address " + address + ": out of range");
        }

        const index = Math.floor(address / 4 / memoryProcLengthVars);
        const x = memoryX + (index % memoryWidth);
        const y = memoryY + Math.floor(index / memoryWidth);

        /** @type {LogicBuild | null} */
        const proc = Vars.world.build(x, y);

        if (proc == null || proc.block.name != "micro-processor") {
            throw new Error(
                "Tried to read invalid address " +
                    address +
                    ": micro-processor not found at " +
                    x +
                    "," +
                    y
            );
        }

        if (
            proc.executor.vars.length != memoryProcLengthVars + 1 ||
            proc.executor.vars[1].name != "!!"
        ) {
            throw new Error(
                "Tried to read invalid address " + address + ": incorrect variable layout"
            );
        }

        return proc;
    }

    /**
     * Calls callback on every word in memory. Return true to keep iterating or false to stop.
     * @param {(word: LVar, address: number) => boolean} callback
     * @param {(bytes: number) => any} onProgress
     * @param {(bytes: number) => any} onFinish
     * @param {(e: Error) => any} onError
     * @param {number} startAddress
     */
    function forEach(callback, onProgress, onFinish, onError, startAddress) {
        let address = startAddress;
        try {
            for (let i = 0; i < 128; i++) {
                let proc = getProcessor(address);
                for (let lvarIndex = 1; lvarIndex <= memoryProcLengthVars; lvarIndex++) {
                    const lvar = proc.executor.vars[lvarIndex];
                    if (!callback(lvar, address)) {
                        onFinish(address + 4);
                        return;
                    }
                    address += 4;
                }
                onProgress(address);
            }
        } catch (e) {
            onError(e);
            return;
        }

        Time.runTask(1, () => forEach(callback, onProgress, onFinish, onError, address));
    }

    /**
     * @param {Fi} file
     * @param {(progress: number, total: number) => any} onProgress
     * @param {(bytes: number) => any} onFinish
     * @param {(e: Error) => any} onError
     */
    function flash(file, onProgress, onFinish, onError) {
        /** @type number[] */
        const data = file.readBytes();
        if (data.length % 4 != 0) {
            onError(new Error("Invalid data alignment, length must be a multiple of 4 bytes!"));
            return;
        } else if (data.length > memoryLengthBytes) {
            onError(new Error("Data too large!"));
            return;
        }

        forEach(
            (word, address) => {
                const value =
                    ((data[address] & 0xff) << 24) |
                    ((data[address + 1] & 0xff) << 16) |
                    ((data[address + 2] & 0xff) << 8) |
                    (data[address + 3] & 0xff);
                word.setnum(value >>> 0);
                return address + 4 < data.length;
            },
            (bytes) => onProgress(bytes, data.length),
            onFinish,
            onError,
            0
        );
    }

    /**
     * @param {Fi} file
     * @param {(progress: number, total: number) => any} onProgress
     * @param {(bytes: number) => any} onFinish
     * @param {(e: Error) => any} onError
     */
    function dump(file, onProgress, onFinish, onError) {
        const writes = file.writes();
        forEach(
            (word, address) => {
                writes.b(((word.numval >> 24) & 0xff) >>> 0);
                writes.b(((word.numval >> 16) & 0xff) >>> 0);
                writes.b(((word.numval >> 8) & 0xff) >>> 0);
                writes.b((word.numval & 0xff) >>> 0);
                return address + 4 < memoryLengthBytes;
            },
            (bytes) => onProgress(bytes, memoryLengthBytes),
            (bytes) => {
                writes.close();
                onFinish(bytes);
            },
            onError,
            0
        );
    }

    return (method) => {
        if (method == "getProcessor") return getProcessor;
        if (method == "forEach") return forEach;
        if (method == "flash") return flash;
        if (method == "dump") return dump;
        throw new Error("Unsupported method: " + method);
    };
};

/**
 * @param {LogicBuild} build
 * @returns {Mlogv32Memory | null}
 */
function Mlogv32Memory_of(build) {
    const x = build.executor.optionalVar("MEMORY_X");
    const y = build.executor.optionalVar("MEMORY_Y");
    const width = build.executor.optionalVar("MEMORY_WIDTH");
    const lengthBytes = build.executor.optionalVar("MEMORY_END");
    const procLengthVars = build.executor.optionalVar("MEMORY_PROC_SIZE");
    if (x == null || y == null || width == null || lengthBytes == null || procLengthVars == null) {
        return null;
    }
    return Mlogv32Memory_new(
        x.numval,
        y.numval,
        width.numval,
        lengthBytes.numval,
        procLengthVars.numval
    );
}
