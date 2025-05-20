function loadRamProcs() {
    Vars.platform.showFileChooser(true, "bin", (file) => {
        const RAM_X = 1;
        const RAM_Y = 1;
        const RAM_WIDTH = 128;
        const RAM_HEIGHT = 128;
        const RAM_PROC_SIZE = 4096;

        const data = file.readBytes();
        if (data.length % 4 != 0) {
            throw new Error("Invalid data alignment, length must be a multiple of 4 bytes!");
        }

        let ramIndex = 0;
        let varIndex = 1; /* 0 is @counter */

        let ram;
        function getRam() {
            const x = RAM_X + (ramIndex % RAM_WIDTH);
            const y = RAM_Y + Math.floor(ramIndex / RAM_WIDTH);
            if (y >= RAM_Y + RAM_HEIGHT) {
                throw new Error(
                    "Data too large, tried to write to nonexistent RAM proc at " + x + "," + y
                );
            }

            ram = Vars.world.build(x, y);
            if (ram.executor.vars[1].name != "!!") {
                throw new Error("Tried to write to invalid RAM proc at " + x + "," + y);
            }
        }
        getRam();

        for (let i = 0; i < data.length; i += 4) {
            if (varIndex >= RAM_PROC_SIZE) {
                ramIndex++;
                varIndex = 1;
                getRam();
            }

            const value =
                ((data[i] & 0xff) << 24) |
                ((data[i + 1] & 0xff) << 16) |
                ((data[i + 2] & 0xff) << 8) |
                (data[i + 3] & 0xff);

            /* i hate javascript */
            ram.executor.vars[varIndex].setnum(value >>> 0);
            varIndex++;
        }

        print(
            "Done! Loaded " +
                data.length +
                " bytes from " +
                file.name() +
                " into " +
                (ramIndex + 1) +
                " RAM procs."
        );
    });
}
