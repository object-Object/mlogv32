use core::marker::PhantomData;

#[derive(derive_mmio::Mmio)]
#[mmio(no_ctors)]
#[repr(C)]
pub struct MachineTimer {
    mtime: u64,
    mtimecmp: u64,
}

impl MachineTimer {
    pub const unsafe fn new_mmio() -> MmioMachineTimer<'static> {
        MmioMachineTimer {
            ptr: 0xf000_0000 as *mut MachineTimer,
            phantom: PhantomData,
        }
    }
}
