package gay.`object`.mlogv32

import arc.files.Fi
import arc.util.Timer
import mindustry.Vars
import mindustry.gen.Building
import mindustry.world.blocks.logic.LogicBlock.LogicBuild
import mindustry.world.blocks.logic.SwitchBlock.SwitchBuild

data class ProcessorAccess(
    val build: LogicBuild,
    val memoryX: Int,
    val memoryY: Int,
    val memoryWidth: Int,
    val romByteOffset: Int,
    val romProcSize: Int,
    val romStart: Int,
    val romEnd: Int,
    val ramProcSize: Int,
    val ramStart: Int,
    val ramEnd: Int,
    val resetSwitch: SwitchBuild,
) {
    val romSize = romEnd - romStart
    val ramSize = ramEnd - ramStart

    fun flashRom(file: Fi): Int {
        val data = file.readBytes()
        require(data.size.mod(4) == 0) { "Data length must be a multiple of 4 bytes." }
        require(data.size <= romSize) { "Data is too large to fit into the processor's ROM." }

        var address = romStart
        val bytes = mutableListOf<Byte>()
        for (byte in data) {
            bytes.add(byte)

            if (bytes.size == romProcSize) {
                flashRomProc(address, bytes)
                bytes.clear()
                address += romProcSize
            }
        }

        if (bytes.isNotEmpty()) {
            flashRomProc(address, bytes)
            bytes.clear()
        }

        return data.size
    }

    fun dumpRam(file: Fi): Int {
        dumpRam(file, ramStart, ramSize)
        return ramSize
    }

    fun dumpRam(file: Fi, startAddress: Int, bytes: Int) {
        require(bytes > 0) { "Bytes must be positive." }
        require(bytes <= ramSize) { "Bytes must not be greater than the RAM size." }
        require(bytes.mod(4) == 0) { "Bytes must be aligned to 4 bytes." }

        val writes = file.writes()
        for ((lvar, _) in ramWordsSequence(startAddress).take(bytes / 4)) {
            val word = lvar.numval.toUInt()
            writes.b(((word shr 24) and 0xffu).toInt())
            writes.b(((word shr 16) and 0xffu).toInt())
            writes.b(((word shr 8) and 0xffu).toInt())
            writes.b((word and 0xffu).toInt())
        }
        writes.close()
    }

    private fun ramWordsSequence(startAddress: Int = 0) = sequence {
        require(startAddress in ramStart..<ramEnd) { "Start address must be within RAM." }
        require(startAddress.mod(4) == 0) { "Start address must be aligned to 4 bytes." }

        var address = startAddress
        while (address < ramEnd) {
            val proc = getRamProc(address) ?: break
            val startIndex = (address / 4).mod(ramProcSize) + 1
            for (i in startIndex..ramProcSize) {
                yield(proc.executor.vars[i]!! to address)
                address += 4
            }
        }
    }

    private fun getRomProc(address: Int): LogicBuild? {
        if (address !in romStart..<romEnd) return null

        val index = address / romProcSize
        val x = memoryX + index.mod(memoryWidth)
        val y = memoryY + index / memoryWidth

        val proc = Vars.world.build(x, y) as? LogicBuild ?: return null

        if (proc.executor.optionalVar("v") == null) return null

        return proc
    }

    private fun flashRomProc(address: Int, data: Iterable<Byte>) {
        val code = buildString {
            append("set v \"")
            for (byte in data) {
                val char = (byte.toInt() and 0xff) + romByteOffset
                append(char.toChar())
            }
            append("\"\nstop")
        }

        val proc = getRomProc(address)
            ?: throw IllegalStateException("ROM proc not found at address: $address")

        proc.updateCode(code)
    }

    private fun getRamProc(address: Int): LogicBuild? {
        if (address !in ramStart..<ramEnd) return null

        // each ROM and RAM proc currently holds the same amount of data, so this doesn't matter too much
        val index = address / 4 / ramProcSize
        val x = memoryX + index.mod(memoryWidth)
        val y = memoryY + index / memoryWidth

        val proc = Vars.world.build(x, y) as? LogicBuild ?: return null

        if (
            proc.executor.vars.size != ramProcSize + 1
            || proc.executor.vars[1].name != "!!"
        ) return null

        return proc
    }

    companion object {
        fun of(build: LogicBuild): ProcessorAccess? {
            return ProcessorAccess(
                build,
                memoryX = nonZeroIntVar(build, "MEMORY_X") ?: return null,
                memoryY = nonZeroIntVar(build, "MEMORY_Y") ?: return null,
                memoryWidth = positiveIntVar(build, "MEMORY_WIDTH") ?: return null,
                romByteOffset = nonNegativeIntVar(build, "ROM_BYTE_OFFSET") ?: return null,
                romProcSize = positiveIntVar(build, "ROM_PROC_SIZE") ?: return null,
                romStart = nonNegativeIntVar(build, "ROM_START") ?: return null,
                romEnd = nonNegativeIntVar(build, "ROM_END") ?: return null,
                ramProcSize = positiveIntVar(build, "RAM_PROC_SIZE") ?: return null,
                ramStart = nonNegativeIntVar(build, "RAM_START") ?: return null,
                ramEnd = nonNegativeIntVar(build, "RAM_END") ?: return null,
                resetSwitch = buildVar<SwitchBuild>(build, "RESET_SWITCH") ?: return null,
            )
        }
    }
}

private fun nonZeroIntVar(build: LogicBuild, name: String): Int? =
    build.executor.optionalVar(name)
        ?.takeIf { !it.isobj }
        ?.numi()
        ?.takeIf { it != 0 }

private fun nonNegativeIntVar(build: LogicBuild, name: String): Int? =
    build.executor.optionalVar(name)
        ?.takeIf { !it.isobj }
        ?.numi()
        ?.takeIf { it >= 0 }

private fun positiveIntVar(build: LogicBuild, name: String): Int? =
    nonZeroIntVar(build, name)
        ?.takeIf { it > 0 }

private inline fun <reified T : Building> buildVar(build: LogicBuild, name: String): T? =
    build.executor.optionalVar(name)?.obj() as? T
