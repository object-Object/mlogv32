package gay.`object`.mlogv32

import arc.Core
import arc.files.Fi
import arc.util.Log
import io.ktor.network.selector.*
import io.ktor.network.sockets.*
import io.ktor.utils.io.*
import kotlinx.coroutines.*
import kotlinx.coroutines.CancellationException
import kotlinx.io.readUByte
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
import kotlin.math.min

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
    val powerSwitch: SwitchBuild,
    val pauseSwitch: SwitchBuild,
    val singleStepSwitch: SwitchBuild,
    uartFifoModulo: Int,
    uart0: MemoryBuild,
    uart1: MemoryBuild,
    uart2: MemoryBuild,
    uart3: MemoryBuild,
) {
    val uart0 = UartAccess(uart0, uartFifoModulo - 1)
    val uart1 = UartAccess(uart1, uartFifoModulo - 1)
    val uart2 = UartAccess(uart2, uartFifoModulo - 1)
    val uart3 = UartAccess(uart3, uartFifoModulo - 1)

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
                            while (true) {
                                Log.info("Waiting for clients...")
                                val client = serverSocket.accept()

                                if (runOnMainThread { build.isValid }) {
                                    Log.info("Client connected!")
                                    launch {
                                        handleClient(client)
                                    }
                                } else {
                                    Log.err("ProcessorAccess build invalid, stopping server.")
                                    client.close()
                                    break
                                }
                            }
                        }
                    } catch (_: CancellationException) {
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

    private fun getCSR(address: Int): UInt =
        csrs.executor.optionalVar(address + 1)
            ?.numu()
            ?: 0u

    private fun getUIntVar(name: String) =
        build.executor.optionalVar(name)?.numu() ?: 0u

    fun getStatus() = StatusResponse(
        running = powerSwitch.enabled,
        paused = pauseSwitch.enabled,
        state = (build.executor.optionalVar("state")?.obj() as? String) ?: "",
        errorOutput = errorOutput.message?.toString() ?: "",
        pc = build.executor.optionalVar("pc")?.numu(),
        instruction = build.executor.optionalVar("instruction")?.numu(),
        privilegeMode = build.executor.optionalVar("privilege_mode")?.numu(),
        registers = registers.memory.take(32).map { it.toUInt() },
        mscratch = getCSR(0x340),
        mtvec = getCSR(0x305),
        mepc = getCSR(0x341),
        mcause = getCSR(0x342),
        mtval = getCSR(0x343),
        mstatus = getUIntVar("csr_mstatus"),
        mip = getUIntVar("csr_mip"),
        mie = getUIntVar("csr_mie"),
        mcycle = (getCSR(0xB80).toULong() shl 32) or getUIntVar("csr_mcycle").toULong(),
        minstret = (getCSR(0xB82).toULong() shl 32) or getUIntVar("csr_minstret").toULong(),
        mtime = (getUIntVar("csr_mtimeh").toULong() shl 32) or getUIntVar("csr_mtime").toULong(),
    )

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

    private suspend fun handleClient(client: Socket) {
        client.use {
            val rx = client.openReadChannel()
            val tx = client.openWriteChannel(true)
            while (true) {
                val response: Response? = try {
                    val line = rx.readUTF8Line() ?: break
                    Log.info("Got request: $line")
                    val request = Json.decodeFromString<Request>(line)
                    request.handle(this@ProcessorAccess, rx, tx)
                } catch (e: CancellationException) {
                    throw e
                } catch (e: IllegalArgumentException) {
                    Log.err("Bad request", e)
                    ErrorResponse.badRequest(e)
                } catch (e: ClosedByteChannelException) {
                    break
                } catch (e: Exception) {
                    Log.err("Request failed", e)
                    ErrorResponse(e)
                }
                if (response == null) {
                    Log.info("Disconnecting from client.")
                    break
                }
                tx.writeStringUtf8(Json.encodeToString(response) + "\n")
            }
            Log.info("Client disconnected.")
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
                powerSwitch = buildVar<SwitchBuild>(build, "switch1") ?: return null,
                pauseSwitch = buildVar<SwitchBuild>(build, "switch2") ?: return null,
                singleStepSwitch = buildVar<SwitchBuild>(build, "switch3") ?: return null,
                uartFifoModulo = positiveIntVar(build, "UART_FIFO_MODULO") ?: return null,
                uart0 = buildVar<MemoryBuild>(build, "bank1") ?: return null,
                uart1 = buildVar<MemoryBuild>(build, "bank2") ?: return null,
                uart2 = buildVar<MemoryBuild>(build, "bank3") ?: return null,
                uart3 = buildVar<MemoryBuild>(build, "bank4") ?: return null,
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
        .firstOrNull { it.valid && it.name == name }
        ?.let { Vars.world.build(it.x, it.y) }

private fun LVar.numu() = num().toUInt()

private suspend fun <T> runOnMainThread(block: () -> T): T {
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

@Serializable
sealed class Request {
    abstract suspend fun handle(processor: ProcessorAccess, rx: ByteReadChannel, tx: ByteWriteChannel): Response?
}

@Serializable
@SerialName("flash")
data class FlashRequest(
    val path: String,
    val absolute: Boolean = true,
) : Request() {
    override suspend fun handle(processor: ProcessorAccess, rx: ByteReadChannel, tx: ByteWriteChannel) = runOnMainThread {
        val file = if (absolute) {
            Core.files.absolute(path)
        } else {
            Core.files.local(path)
        }
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
    val absolute: Boolean = true,
) : Request() {
    override suspend fun handle(processor: ProcessorAccess, rx: ByteReadChannel, tx: ByteWriteChannel) = runOnMainThread {
        val file = if (absolute) {
            Core.files.absolute(path)
        } else {
            Core.files.local(path)
        }
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
    override suspend fun handle(processor: ProcessorAccess, rx: ByteReadChannel, tx: ByteWriteChannel) = runOnMainThread {
        processor.singleStepSwitch.configure(singleStep)
        processor.powerSwitch.configure(true)
        SuccessResponse("Processor started.")
    }
}

@Serializable
@SerialName("wait")
data class WaitRequest(
    val stopped: Boolean,
    val paused: Boolean,
) : Request() {
    override suspend fun handle(processor: ProcessorAccess, rx: ByteReadChannel, tx: ByteWriteChannel): Response {
        while (true) {
            delay(1000/60) // 1 tick
            val (running, paused) = runOnMainThread {
                processor.powerSwitch.enabled to processor.pauseSwitch.enabled
            }
            if (this.stopped && !running) {
                return SuccessResponse("Processor has stopped.")
            }
            if (this.paused && paused) {
                return SuccessResponse("Processor has paused.")
            }
        }
    }
}

@Serializable
enum class UartDevice {
    uart0,
    uart1,
    uart2,
    uart3,
}

@Serializable
enum class UartDirection {
    both,
    tx,
    rx;

    val transmit get() = this != rx
    val receive get() = this != tx
}

@Serializable
@SerialName("serial")
data class SerialRequest(
    val device: UartDevice,
    val direction: UartDirection = UartDirection.both,
    val stopOnHalt: Boolean = false,
    val disconnectOnHalt: Boolean = false,
) : Request() {
    override suspend fun handle(processor: ProcessorAccess, rx: ByteReadChannel, tx: ByteWriteChannel): Response? {
        val uart = when (device) {
            UartDevice.uart0 -> processor.uart0
            UartDevice.uart1 -> processor.uart1
            UartDevice.uart2 -> processor.uart2
            UartDevice.uart3 -> processor.uart3
        }
        while (true) {
            if (rx.isClosedForRead || tx.isClosedForWrite) {
                throw RuntimeException("Client disconnected!")
            }

            var overflowCount = 0

            val fromUart = runOnMainThread {
                if (!processor.build.isValid) {
                    Log.info("ProcessorAccess build invalid, closing serial connection.")
                    return@runOnMainThread null
                }

                if (!processor.powerSwitch.enabled) {
                    when {
                        disconnectOnHalt -> return@runOnMainThread null
                        stopOnHalt -> throw RuntimeException("Processor stopped!")
                    }
                }

                if (direction.transmit) {
                    rx.readAvailable(1) { buffer ->
                        val bytes = min(buffer.size.toInt(), uart.availableForWrite)

                        for (i in 0..<bytes) {
                            val byte = buffer.readUByte()
                            if (!uart.write(byte)) overflowCount++
                        }

                        bytes
                    }
                }

                if (direction.receive) {
                    uart.readAll()
                } else {
                    listOf()
                }
            } ?: return null

            if (overflowCount > 0) Log.warn("$device RX buffer is full, $overflowCount bytes dropped!")

            for (byte in fromUart) {
                tx.writeByte(byte.toByte())
            }

            delay(1000/60) // 1 tick
        }
    }
}

@Serializable
@SerialName("unpause")
data object UnpauseRequest : Request() {
    override suspend fun handle(processor: ProcessorAccess, rx: ByteReadChannel, tx: ByteWriteChannel) = runOnMainThread {
        require(processor.powerSwitch.enabled) { "Processor is not running!" }
        processor.pauseSwitch.configure(false)
        SuccessResponse("Processor unpaused.")
    }
}

@Serializable
@SerialName("stop")
data object StopRequest : Request() {
    override suspend fun handle(processor: ProcessorAccess, rx: ByteReadChannel, tx: ByteWriteChannel) = runOnMainThread {
        processor.powerSwitch.configure(false)
        processor.pauseSwitch.configure(false)
        processor.singleStepSwitch.configure(false)
        SuccessResponse("Processor stopped.")
    }
}

@Serializable
@SerialName("status")
data object StatusRequest : Request() {
    override suspend fun handle(processor: ProcessorAccess, rx: ByteReadChannel, tx: ByteWriteChannel) = runOnMainThread {
        processor.getStatus()
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
    val state: String,
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
    val mcycle: ULong,
    val minstret: ULong,
    val mtime: ULong,
) : Response()

@Serializable
@SerialName("error")
data class ErrorResponse(val message: String) : Response() {
    constructor(e: Exception) : this("Request failed: $e")

    companion object {
        fun badRequest(e: IllegalArgumentException) = ErrorResponse("Bad request: $e")
    }
}
