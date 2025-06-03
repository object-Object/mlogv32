package gay.`object`.mlogv32

import arc.Core
import arc.util.CommandHandler
import arc.util.Log
import mindustry.Vars
import mindustry.mod.Mod
import mindustry.world.blocks.logic.LogicBlock.LogicBuild

@Suppress("unused")
class Mlogv32UtilsMod : Mod() {
    override fun registerServerCommands(handler: CommandHandler) {
        handler.register(
            "mlogv32.flash",
            "<x> <y> <file>",
            "Flash a .bin file to the processor's ROM.",
        ) { (x, y, path) ->
            val processor = getProcessor(x, y) ?: return@register

            val file = if (path.startsWith("/")) {
                Core.files.absolute(path)
            } else {
                Core.files.local(path)
            }
            if (!file.exists()) {
                Log.err("File does not exist.")
                return@register
            }

            val bytes = try {
                processor.flashRom(file)
            } catch (e: Exception) {
                Log.err("Failed to flash file.", e)
                return@register
            }

            Log.info("Successfully flashed $bytes bytes from $file.")
        }

        handler.register(
            "mlogv32.dump",
            "<x> <y> <file> [start-address] [bytes]",
            "Dump the processor's RAM to a file.",
        ) { args ->
            val (x, y, path) = args

            val processor = getProcessor(x, y) ?: return@register

            val file = if (path.startsWith("/")) {
                Core.files.absolute(path)
            } else {
                Core.files.local(path)
            }
            file.parent().mkdirs()

            val startAddress = if (args.size >= 4) {
                val result = args[3].toIntOrNull()
                if (result == null) {
                    Log.err("Failed to parse start address.")
                    return@register
                }
                result
            } else {
                processor.ramStart
            }

            val bytes = if (args.size >= 5) {
                val result = args[4].toIntOrNull()
                if (result == null) {
                    Log.err("Failed to parse bytes.")
                    return@register
                }
                result
            } else {
                processor.ramEnd - startAddress
            }

            try {
                processor.dumpRam(file, startAddress, bytes)
            } catch (e: Exception) {
                Log.err("Failed to dump RAM.", e)
                return@register
            }

            Log.info("Successfully dumped $bytes bytes from processor RAM to $file.")
        }
    }
}

private fun getProcessor(x: String, y: String): ProcessorAccess? {
    val xVal = x.toIntOrNull()
    if (xVal == null) {
        Log.err("Failed to parse x coordinate.")
        return null
    }

    val yVal = y.toIntOrNull()
    if (yVal == null) {
        Log.err("Failed to parse y coordinate.")
        return null
    }

    val build = Vars.world.build(xVal, yVal) as? LogicBuild
    if (build == null) {
        Log.err("Invalid position: no processor found.")
        return null
    }

    val result = ProcessorAccess.of(build)
    if (result == null) {
        Log.err("Invalid position: processor is not a valid mlogv32 CPU.")
        return null
    }

    return result
}
