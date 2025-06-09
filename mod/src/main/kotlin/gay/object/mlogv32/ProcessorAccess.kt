package gay.`object`.mlogv32

import arc.Core
import arc.files.Fi
import arc.util.Log
import io.ktor.network.selector.*
import io.ktor.network.sockets.*
import io.ktor.utils.io.*
import kotlinx.coroutines.*
import kotlinx.coroutines.CancellationException
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import mindustry.Vars
import mindustry.gen.Building
import mindustry.logic.LVar
import mindustry.world.blocks.logic.LogicBlock.LogicBuild
import mindustry.world.blocks.logic.MemoryBlock.MemoryBuild
import mindustry.world.blocks.logic.MessageBlock.MessageBuild
import mindustry.world.blocks.logic.SwitchBlock.SwitchBuild
import kotlin.concurrent.thread
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

class ProcessorAccess(
    val build: LogicBuild,
    val memoryX: Int,
    val memoryY: Int,
    val memoryWidth: Int,
    val romSize: Int,
    val ramSize: Int,
    val registers: MemoryBuild,
    val csrs: LogicBuild,
    val errorOutput: MessageBuild,
    val resetSwitch: SwitchBuild,
    val pauseSwitch: SwitchBuild,
    val singleStepSwitch: SwitchBuild,
) {
    val romEnd = ROM_START + romSize.toUInt()
    val ramEnd = RAM_START + ramSize.toUInt()

    val ramStartProc = (romEnd / ROM_PROC_BYTES.toUInt()).toInt()

    fun flashRom(file: Fi): Int {
        val data = file.readBytes()
        require(data.size.mod(4) == 0) { "Data length must be a multiple of 4 bytes." }
        require(data.size <= romSize) { "Data is too large to fit into the processor's ROM." }

        var address = ROM_START
        val bytes = mutableListOf<Byte>()
        for (byte in data) {
            bytes.add(byte)

            if (bytes.size == ROM_PROC_BYTES) {
                flashRomProc(address, bytes)
                bytes.clear()
                address += ROM_PROC_BYTES.toUInt()
            }
        }

        if (bytes.isNotEmpty()) {
            flashRomProc(address, bytes)
            bytes.clear()
        }

        return data.size
    }

    fun dumpRam(file: Fi): Int {
        dumpRam(file, RAM_START, ramSize)
        return ramSize
    }

    fun dumpRam(file: Fi, startAddress: UInt, bytes: Int) {
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

    fun isServerRunning() = serverThread != null && serverJob != null && serverBuildId == build.id

    fun startServer(hostname: String, port: Int) {
        if (serverThread != null) stopServer()

        Log.info("Starting ProcessorAccess socket server at $hostname:$port for building ${build.id}...")

        serverBuildId = build.id
        serverThread = thread(isDaemon = true) {
            runBlocking {
                serverJob = launch {
                    try {
                        val selector = SelectorManager(Dispatchers.IO)
                        aSocket(selector).tcp().bind(hostname, port).use { serverSocket ->
                            runServer(serverSocket)
                        }
                    } catch (e: Exception) {
                        Log.err("ProcessorAccess server failed", e)
                    }
                }
            }

            // cleanup
            serverJob = null
            serverThread = null
            serverBuildId = null

            Log.info("ProcessorAccess thread exiting.")
        }
    }

    fun stopServer() {
        ProcessorAccess.stopServer()
    }

    fun getCSR(address: Int): UInt =
        csrs.executor.optionalVar(address + 1)
            ?.numu()
            ?: 0u

    private fun ramWordsSequence(startAddress: UInt) = sequence {
        require(startAddress in RAM_START..<ramEnd) { "Start address must be within RAM." }
        require(startAddress.mod(4u) == 0u) { "Start address must be aligned to 4 bytes." }

        var address = startAddress
        while (address < ramEnd) {
            val (proc, startIndex) = getRamProc(address) ?: break
            for (i in startIndex..<RAM_PROC_VARS) {
                yield(proc.executor.vars[i + 1]!! to address)
                address += 4u
            }
        }
    }

    private fun getRomProc(address: UInt): LogicBuild? {
        if (address !in ROM_START..<romEnd) return null

        val index = (address / ROM_PROC_BYTES.toUInt()).toInt()
        val x = memoryX + index.mod(memoryWidth)
        val y = memoryY + index / memoryWidth

        val proc = Vars.world.build(x, y) as? LogicBuild ?: return null

        if (proc.executor.optionalVar("v") == null) return null

        return proc
    }

    private fun flashRomProc(address: UInt, data: Iterable<Byte>) {
        val code = buildString {
            append("set v \"")
            for (byte in data) {
                val char = (byte.toInt() and 0xff) + ROM_BYTE_OFFSET
                append(char.toChar())
            }
            append("\"\nstop")
        }

        val proc = getRomProc(address)
            ?: throw IllegalStateException("ROM proc not found at address: $address")

        proc.updateCode(code)
    }

    private fun getRamProc(address: UInt): Pair<LogicBuild, Int>? {
        if (address !in RAM_START..<ramEnd) return null

        val ramAddress = address - RAM_START
        val ramVariable = (ramAddress / 4u).toInt()

        // each ROM and RAM proc currently holds the same amount of data, so this doesn't matter too much
        val index = ramStartProc + ramVariable / RAM_PROC_VARS
        val x = memoryX + index.mod(memoryWidth)
        val y = memoryY + index / memoryWidth

        val proc = Vars.world.build(x, y) as? LogicBuild ?: return null

        if (
            proc.executor.vars.size != RAM_PROC_VARS + 1
            || proc.executor.vars[1].name != "!!"
        ) return null

        return proc to ramVariable.mod(RAM_PROC_VARS)
    }

    private suspend fun runServer(serverSocket: ServerSocket) {
        while (true) {
            Log.info("Waiting for clients...")
            serverSocket.accept().use { client ->
                Log.info("Client connected!")
                val rx = client.openReadChannel()
                val tx = client.openWriteChannel(true)
                while (true) {
                    val response: Response = try {
                        val line = rx.readUTF8Line() ?: break
                        Log.info("Got request: $line")
                        val request = Json.decodeFromString<Request>(line)
                        request.handle(this)
                    } catch (e: CancellationException) {
                        throw e
                    } catch (e: IllegalArgumentException) {
                        Log.err("Bad request", e)
                        ErrorResponse.badRequest(e)
                    } catch (e: Exception) {
                        Log.err("Request failed", e)
                        ErrorResponse(e)
                    }
                    tx.writeStringUtf8(Json.encodeToString(response) + "\n")
                }
                Log.info("Client disconnected.")
            }
        }
    }

    companion object {
        const val ROM_BYTE_OFFSET = 174
        const val ROM_PROC_BYTES = 16384
        const val RAM_PROC_VARS = 4096

        const val ROM_START = 0x00000000u
        const val RAM_START = 0x80000000u

        private var serverThread: Thread? = null
        private var serverJob: Job? = null
        private var serverBuildId: Int? = null

        fun of(build: LogicBuild): ProcessorAccess? {
            return ProcessorAccess(
                build,
                memoryX = nonZeroIntVar(build, "MEMORY_X") ?: return null,
                memoryY = nonZeroIntVar(build, "MEMORY_Y") ?: return null,
                memoryWidth = positiveIntVar(build, "MEMORY_WIDTH") ?: return null,
                romSize = positiveIntVar(build, "ROM_SIZE") ?: return null,
                ramSize = positiveIntVar(build, "RAM_SIZE") ?: return null,
                registers = buildVar<MemoryBuild>(build, "cell1") ?: return null,
                csrs = buildVar<LogicBuild>(build, "processor17") ?: return null,
                errorOutput = buildVar<MessageBuild>(build, "message1") ?: return null,
                resetSwitch = buildVar<SwitchBuild>(build, "switch1") ?: return null,
                pauseSwitch = buildVar<SwitchBuild>(build, "switch2") ?: return null,
                singleStepSwitch = buildVar<SwitchBuild>(build, "switch3") ?: return null,
            )
        }

        fun stopServer() {
            if (serverThread == null) return
            Log.info("Stopping ProcessorAccess server for building $serverBuildId...")
            serverJob?.cancel()
            serverThread?.join()
            Log.info("Stopped ProcessorAccess server.")
        }
    }
}

private fun nonZeroIntVar(build: LogicBuild, name: String): Int? =
    build.executor.optionalVar(name)
        ?.takeIf { !it.isobj }
        ?.numi()
        ?.takeIf { it != 0 }

private fun positiveIntVar(build: LogicBuild, name: String): Int? =
    nonZeroIntVar(build, name)
        ?.takeIf { it > 0 }

private inline fun <reified T : Building> buildVar(build: LogicBuild, name: String): T? =
    (build.executor.optionalVar(name)?.obj() ?: linkedBuild(build, name)) as? T

// why
private fun linkedBuild(build: LogicBuild, name: String) =
    build.links
        .firstOrNull { it.active && it.valid && it.name == name }
        ?.let { Vars.world.build(it.x, it.y) }

private fun LVar.numu() = num().toUInt()

@Serializable
sealed class Request {
    abstract suspend fun handle(processor: ProcessorAccess): Response

    protected suspend fun <T> runOnMainThread(block: () -> T): T {
        return suspendCancellableCoroutine { continuation ->
            Core.app.post {
                try {
                    continuation.resume(block())
                } catch (e: Exception) {
                    continuation.resumeWithException(e)
                }
            }
        }
    }
}

@Serializable
@SerialName("flash")
data class FlashRequest(
    val path: String,
) : Request() {
    override suspend fun handle(processor: ProcessorAccess) = runOnMainThread {
        val file = Core.files.absolute(path)
        require(file.exists()) { "File not found." }

        val bytes = processor.flashRom(file)
        SuccessResponse("Successfully flashed $bytes bytes from $file to ROM.")
    }
}

@Serializable
@SerialName("dump")
data class DumpRequest(
    val path: String,
    val address: UInt?,
    val bytes: Int?,
) : Request() {
    override suspend fun handle(processor: ProcessorAccess) = runOnMainThread {
        val file = Core.files.absolute(path)
        file.parent().mkdirs()

        val address = address ?: ProcessorAccess.RAM_START
        val bytes = bytes ?: (processor.ramEnd - address).toInt()

        processor.dumpRam(file, address, bytes)
        SuccessResponse("Successfully dumped $bytes bytes from RAM to $file.")
    }
}

@Serializable
@SerialName("start")
data class StartRequest(
    val singleStep: Boolean = false,
) : Request() {
    override suspend fun handle(processor: ProcessorAccess) = runOnMainThread {
        processor.singleStepSwitch.configure(singleStep)
        processor.resetSwitch.configure(false)
        SuccessResponse("Processor started.")
    }
}

@Serializable
@SerialName("wait")
data class WaitRequest(
    val stopped: Boolean,
    val paused: Boolean,
) : Request() {
    override suspend fun handle(processor: ProcessorAccess): Response {
        while (true) {
            delay(1000/60) // 1 tick
            val (stopped, paused) = runOnMainThread {
                processor.resetSwitch.enabled to processor.pauseSwitch.enabled
            }
            if (this.stopped && stopped) {
                return SuccessResponse("Processor has stopped.")
            }
            if (this.paused && paused) {
                return SuccessResponse("Processor has paused.")
            }
        }
    }
}

@Serializable
@SerialName("unpause")
data object UnpauseRequest : Request() {
    override suspend fun handle(processor: ProcessorAccess) = runOnMainThread {
        require(!processor.resetSwitch.enabled) { "Processor is not running!" }
        processor.pauseSwitch.configure(false)
        SuccessResponse("Processor unpaused.")
    }
}

@Serializable
@SerialName("stop")
data object StopRequest : Request() {
    override suspend fun handle(processor: ProcessorAccess) = runOnMainThread {
        processor.resetSwitch.configure(true)
        processor.pauseSwitch.configure(false)
        processor.singleStepSwitch.configure(false)
        SuccessResponse("Processor stopped.")
    }
}

@Serializable
@SerialName("status")
data object StatusRequest : Request() {
    override suspend fun handle(processor: ProcessorAccess) = runOnMainThread {
        StatusResponse(
            running = !processor.resetSwitch.enabled,
            paused = processor.pauseSwitch.enabled,
            errorOutput = processor.errorOutput.message?.toString() ?: "",
            pc = processor.build.executor.optionalVar("pc")?.numu(),
            instruction = processor.build.executor.optionalVar("instruction")?.numu(),
            privilegeMode = processor.build.executor.optionalVar("privilege_mode")?.numu(),
            registers = processor.registers.memory.take(32).map { it.toUInt() },
            mscratch = processor.getCSR(0x340),
            mtvec = processor.getCSR(0x305),
            mepc = processor.getCSR(0x341),
            mcause = processor.getCSR(0x342),
            mtval = processor.getCSR(0x343),
            mstatus = processor.getCSR(0x300),
            mip = processor.getCSR(0x344),
            mie = processor.getCSR(0x304),
        )
    }
}

@Serializable
sealed class Response

@Serializable
@SerialName("success")
data class SuccessResponse(val message: String) : Response()

@Serializable
@SerialName("status")
data class StatusResponse(
    val running: Boolean,
    val paused: Boolean,
    val errorOutput: String,
    val pc: UInt?,
    val instruction: UInt?,
    val privilegeMode: UInt?,
    val registers: List<UInt>,
    val mscratch: UInt,
    val mtvec: UInt,
    val mepc: UInt,
    val mcause: UInt,
    val mtval: UInt,
    val mstatus: UInt,
    val mip: UInt,
    val mie: UInt,
) : Response()

@Serializable
@SerialName("error")
data class ErrorResponse(val message: String) : Response() {
    constructor(e: Exception) : this("Request failed: $e")

    companion object {
        fun badRequest(e: IllegalArgumentException) = ErrorResponse("Bad request: $e")
    }
}
