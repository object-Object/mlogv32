package gay.`object`.mlogv32

import mindustry.world.blocks.logic.MemoryBlock.MemoryBuild
import kotlin.reflect.KProperty

class UartAccess(private val build: MemoryBuild, private val capacity: Int) {
    // NOTE: rx and tx refer to our receiver and transmitter, not the processor's
    private val txRptr by MemoryIntDelegate(build, 254)
    private var txWptrRaw by MemoryIntDelegate(build, 255)
    private val txWptr get() = txWptrRaw and 0xff

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

        val byte = build.memory[256 + rxRptr].toInt().toUByte()
        rxRptr = wrap(rxRptr + 1)
        return byte
    }

    fun write(byte: UByte, signalOverflow: Boolean = true): Boolean {
        val nextWptr = wrap(txWptr + 1)

        // full, maybe signal overflow
        if (nextWptr == txRptr) {
            if (signalOverflow) {
                txWptrRaw = txWptr or 0x100
            }
            return false
        }

        // not full, write a byte
        build.memory[txWptr] = byte.toDouble()
        txWptrRaw = nextWptr
        return true
    }

    private fun wrap(index: Int) = index.mod(capacity + 1)
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
