package gay.`object`.mlogv32

import arc.Core
import arc.Events
import arc.util.CommandHandler
import arc.util.Log
import mindustry.Vars
import mindustry.core.GameState
import mindustry.game.EventType
import mindustry.mod.Mod
import mindustry.world.blocks.logic.LogicBlock.LogicBuild

@Suppress("unused")
class Mlogv32UtilsMod : Mod() {
    override fun init() {
        Events.on(EventType.StateChangeEvent::class.java) { event ->
            if (event.to == GameState.State.menu) {
                ProcessorAccess.stopServer()
            }
        }
    }

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
                val result = args[3].toUIntOrNull()
                if (result == null) {
                    Log.err("Failed to parse start address.")
                    return@register
                }
                result
            } else {
                ProcessorAccess.RAM_START
            }

            val bytes = if (args.size >= 5) {
                val result = args[4].toIntOrNull()
                if (result == null) {
                    Log.err("Failed to parse bytes.")
                    return@register
                }
                result
            } else {
                (processor.ramEnd - startAddress).toInt()
            }

            try {
                processor.dumpRam(file, startAddress, bytes)
            } catch (e: Exception) {
                Log.err("Failed to dump RAM.", e)
                return@register
            }

            Log.info("Successfully dumped $bytes bytes from processor RAM to $file.")
        }

        handler.register(
            "mlogv32.start",
            "<x> <y>",
            "Start the processor.",
        ) { (x, y) ->
            val processor = getProcessor(x, y) ?: return@register
            processor.powerSwitch.configure(true)
            Log.info("Processor started.")
        }

        handler.register(
            "mlogv32.pause",
            "<x> <y>",
            "Pause the processor.",
        ) { (x, y) ->
            val processor = getProcessor(x, y) ?: return@register
            processor.singleStepSwitch.configure(true)
            processor.pauseSwitch.configure(true)
            Log.info("Processor paused.")
        }

        handler.register(
            "mlogv32.step",
            "<x> <y>",
            "Step the processor by one instruction.",
        ) { (x, y) ->
            val processor = getProcessor(x, y) ?: return@register
            processor.singleStepSwitch.configure(true)
            processor.pauseSwitch.configure(false)
            Log.info("Processor stepped.")
        }

        handler.register(
            "mlogv32.unpause",
            "<x> <y>",
            "Unpause the processor.",
        ) { (x, y) ->
            val processor = getProcessor(x, y) ?: return@register
            processor.singleStepSwitch.configure(false)
            processor.pauseSwitch.configure(false)
            Log.info("Processor unpaused.")
        }

        handler.register(
            "mlogv32.stop",
            "<x> <y>",
            "Stop the processor.",
        ) { (x, y) ->
            val processor = getProcessor(x, y) ?: return@register
            processor.powerSwitch.configure(false)
            Log.info("Processor stopped.")
        }

        handler.register(
            "mlogv32.status",
            "<x> <y>",
            "View the processor's status.",
        ) { (x, y) ->
            val processor = getProcessor(x, y) ?: return@register
            Log.info(processor.getStatus().toPrettyDebugString(indentWidth = 2))
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

// https://gist.github.com/mayankmkh/92084bdf2b59288d3e74c3735cccbf9f?permalink_comment_id=5355537#gistcomment-5355537
private fun Any.toPrettyDebugString(indentWidth : Int = 4) = buildString {
    fun StringBuilder.indent(level : Int) = append("".padStart(level * indentWidth))
    var ignoreSpace = false
    var indentLevel = 0
    this@toPrettyDebugString.toString().onEach {
        when (it) {
            '(', '[', '{' -> appendLine(it).indent(++indentLevel)
            ')', ']', '}' -> appendLine().indent(--indentLevel).append(it)
            ','           -> appendLine(it).indent(indentLevel).also { ignoreSpace = true }
            ' '           -> if (ignoreSpace) ignoreSpace = false else append(it)
            '='           -> append(" = ")
            else          -> append(it)
        }
    }
}
