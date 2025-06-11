package gay.`object`.mlogv32

import mindustry.world.blocks.logic.MemoryBlock.MemoryBuild
import kotlin.reflect.KProperty

class UartAccess(private val build: MemoryBuild, private val capacity: Int) {
    // NOTE: rx and tx refer to our receiver and transmitter, not the processor's
    private val txRptr by MemoryIntDelegate(build, 254)
    private var txWptr by MemoryIntDelegate(build, 255)
    private val txSize get() = (txWptr - txRptr).mod(capacity * 2)

    private var rxRptr by MemoryIntDelegate(build, 510)
    private val rxWptr by MemoryIntDelegate(build, 511)

    fun readAll() : List<UByte>{
        val result = mutableListOf<UByte>()
        while (true) {
            val byte = read() ?: return result
            result.add(byte)
        }
    }

    fun read(): UByte? {
        if (rxRptr == rxWptr) {
            return null
        }

        val byte = build.memory[256 + rxRptr.mod(capacity)].toInt().toUByte()
        rxRptr = (rxRptr + 1).mod(capacity * 2)
        return byte
    }

    fun write(byte: UByte) {
        if (txSize < capacity) {
            build.memory[txWptr.mod(capacity)] = byte.toDouble()
        }
        if (txSize <= capacity) {
            txWptr = (txWptr + 1).mod(capacity * 2)
        }
    }
}

class MemoryIntDelegate(
    private val build: MemoryBuild,
    private val index: Int,
) {
    operator fun getValue(thisRef: Any, property: KProperty<*>): Int {
        return build.memory[index].toInt()
    }

    operator fun setValue(thisRef: Any, property: KProperty<*>, value: Int) {
        build.memory[index] = value.toDouble()
    }
}
