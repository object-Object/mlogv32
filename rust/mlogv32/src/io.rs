use core::{hint, slice};

use bitbybit::bitfield;
use derive_mmio::Mmio;
use embassy_hal_internal::atomic_ring_buffer::RingBuffer;

pub fn print_str(msg: &str) {
    for c in msg.chars() {
        print_char(c);
    }
}

pub fn print_char(_c: char) {
    // FIXME: printchar instruction no longer exists, set up println impl similar to esp-println
    // https://github.com/esp-rs/esp-hal/tree/84bb51215d261913f00239ecd0ed38fcd8296d0e/esp-println
}

// TODO: create Peripherals struct?

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum UartAddress {
    Uart0,
    Uart1,
    Uart2,
    Uart3,
}

impl UartAddress {
    pub fn addr(&self) -> usize {
        match self {
            Self::Uart0 => 0xf0000010,
            Self::Uart1 => 0xf0000020,
            Self::Uart2 => 0xf0000030,
            Self::Uart3 => 0xf0000040,
        }
    }

    pub fn ptr(&self) -> *mut Uart {
        self.addr() as *mut Uart
    }
}

#[bitfield(u32)]
pub struct UartStatus {
    #[bit(7, r)]
    pub parity_error: bool,
    #[bit(6, r)]
    pub frame_error: bool,
    #[bit(5, r)]
    pub overrun_error: bool,
    #[bit(4, r)]
    pub interrupts: bool,
    #[bit(3, r)]
    pub tx_full: bool,
    #[bit(2, r)]
    pub tx_empty: bool,
    #[bit(1, r)]
    pub rx_full: bool,
    #[bit(0, r)]
    pub rx_not_empty: bool,
}

#[bitfield(u32)]
pub struct UartControl {
    #[bit(4, w)]
    pub interrupts: bool,
    #[bit(1, w)]
    pub reset_rx: bool,
    #[bit(0, w)]
    pub reset_tx: bool,
}

#[derive(Mmio)]
#[mmio(no_ctors)]
#[repr(C)]
pub struct Uart {
    #[mmio(Read)]
    rx: u32,
    #[mmio(Write)]
    tx: u32,
    #[mmio(Read)]
    status: UartStatus,
    #[mmio(Write)]
    control: UartControl,
}

impl Uart {
    /// # Safety
    ///
    /// This function is unsafe because the caller must ensure that only one instance of each device exists at a time, as it represents a physical memory-mapped peripheral.
    pub unsafe fn new_mmio(addr: UartAddress) -> MmioUart<'static> {
        MmioUart {
            ptr: addr.ptr(),
            phantom: core::marker::PhantomData,
        }
    }
}

pub struct UartPort {
    uart: MmioUart<'static>,
}

impl UartPort {
    /// # Safety
    ///
    /// This function is unsafe because the caller must ensure that only one instance of each device exists at a time, as it represents a physical memory-mapped peripheral.
    pub unsafe fn new(addr: UartAddress) -> Self {
        Self {
            uart: unsafe { Uart::new_mmio(addr) },
        }
    }

    pub fn init(&mut self) {
        self.uart.write_control(
            UartControl::ZERO
                .with_interrupts(false)
                .with_reset_rx(true)
                .with_reset_tx(true),
        );
    }

    pub fn clear(&mut self) {
        self.uart
            .write_control(UartControl::ZERO.with_reset_rx(true).with_reset_tx(true));
    }

    pub fn uart_mut(&mut self) -> &mut MmioUart<'static> {
        &mut self.uart
    }

    pub fn read(&mut self, buf: &mut [u8]) -> usize {
        for (i, item) in buf.iter_mut().enumerate() {
            if let Some(byte) = self.read_byte() {
                *item = byte;
            } else {
                return i;
            }
        }
        buf.len()
    }

    pub fn read_byte(&mut self) -> Option<u8> {
        if self.has_data() {
            Some(self.uart.read_rx() as u8)
        } else {
            None
        }
    }

    pub fn has_data(&mut self) -> bool {
        self.uart.read_status().rx_not_empty()
    }

    pub fn blocking_write(&mut self, buf: &[u8]) {
        for &byte in buf {
            self.write_byte(byte);
        }
    }

    pub fn write(&mut self, buf: &[u8]) -> usize {
        for (i, &byte) in buf.iter().enumerate() {
            if !self.try_write_byte(byte) {
                return i;
            }
        }
        buf.len()
    }

    pub fn write_byte(&mut self, byte: u8) {
        while !self.try_write_byte(byte) {
            hint::spin_loop();
        }
    }

    pub fn try_write_byte(&mut self, byte: u8) -> bool {
        if !self.can_write() {
            return false;
        }
        self.uart.write_tx(byte as u32);
        true
    }

    pub fn can_write(&mut self) -> bool {
        !self.uart.read_status().tx_full()
    }
}

#[derive(Debug, PartialEq, Eq, Clone, Copy)]
pub enum Error {
    Overrun,
}

impl embedded_io::Error for Error {
    fn kind(&self) -> embedded_io::ErrorKind {
        embedded_io::ErrorKind::Other
    }
}

impl embedded_io_async::ErrorType for UartPort {
    type Error = Error;
}

impl embedded_io_async::ReadReady for UartPort {
    fn read_ready(&mut self) -> Result<bool, Self::Error> {
        Ok(self.has_data())
    }
}

impl embedded_io_async::Read for UartPort {
    async fn read(&mut self, buf: &mut [u8]) -> Result<usize, Self::Error> {
        if buf.is_empty() {
            return Ok(0);
        }

        while !self.has_data() {
            embassy_futures::yield_now().await;
        }

        if self.uart.read_status().overrun_error() {
            return Err(Error::Overrun);
        }

        Ok(self.read(buf))
    }
}

impl embedded_io_async::WriteReady for UartPort {
    fn write_ready(&mut self) -> Result<bool, Self::Error> {
        Ok(self.can_write())
    }
}

impl embedded_io_async::Write for UartPort {
    async fn write(&mut self, buf: &[u8]) -> Result<usize, Self::Error> {
        if buf.is_empty() {
            return Ok(0);
        }

        while !self.can_write() {
            embassy_futures::yield_now().await;
        }

        Ok(self.write(buf))
    }
}

impl embedded_io::Read for UartPort {
    fn read(&mut self, buf: &mut [u8]) -> Result<usize, Self::Error> {
        if buf.is_empty() {
            return Ok(0);
        }

        while !self.has_data() {
            hint::spin_loop();
        }

        if self.uart.read_status().overrun_error() {
            return Err(Error::Overrun);
        }

        Ok(self.read(buf))
    }
}

impl embedded_io::Write for UartPort {
    fn write(&mut self, buf: &[u8]) -> Result<usize, Self::Error> {
        if buf.is_empty() {
            return Ok(0);
        }

        while !self.can_write() {
            hint::spin_loop();
        }

        Ok(self.write(buf))
    }

    fn flush(&mut self) -> Result<(), Self::Error> {
        Ok(())
    }
}

// FIXME: this is probably not the correct way to do this
unsafe impl Send for UartPort {}

pub struct BufferedUartPort {
    inner: UartPort,
    buf: RingBuffer,
}

impl BufferedUartPort {
    pub fn new(uart: UartPort, buf: &'static mut [u8]) -> Self {
        let ring_buffer = RingBuffer::new();
        unsafe {
            ring_buffer.init(buf.as_mut_ptr(), buf.len());
        }
        Self {
            inner: uart,
            buf: ring_buffer,
        }
    }

    pub fn init(&mut self) {
        self.inner.init();
    }

    pub fn clear(&mut self) {
        self.inner.clear();
    }
}

impl embedded_io_async::ErrorType for BufferedUartPort {
    type Error = Error;
}

impl embedded_io_async::BufRead for BufferedUartPort {
    async fn fill_buf(&mut self) -> Result<&[u8], Self::Error> {
        if self.buf.is_empty() {
            while !self.inner.has_data() {
                embassy_futures::yield_now().await;
            }

            let mut writer = unsafe { self.buf.writer() };
            let buf = writer.push_slice();
            let n = embedded_io::Read::read(&mut self.inner, buf)?;
            writer.push_done(n);
        }

        let mut reader = unsafe { self.buf.reader() };
        let (p, n) = reader.pop_buf();
        let buf = unsafe { slice::from_raw_parts(p, n) };
        Ok(buf)
    }

    fn consume(&mut self, amt: usize) {
        let mut reader = unsafe { self.buf.reader() };
        reader.pop_done(amt);
    }
}

impl embedded_io_async::ReadReady for BufferedUartPort {
    fn read_ready(&mut self) -> Result<bool, Self::Error> {
        embedded_io_async::ReadReady::read_ready(&mut self.inner)
    }
}

impl embedded_io_async::Read for BufferedUartPort {
    async fn read(&mut self, buf: &mut [u8]) -> Result<usize, Self::Error> {
        embedded_io_async::Read::read(&mut self.inner, buf).await
    }
}

impl embedded_io_async::WriteReady for BufferedUartPort {
    fn write_ready(&mut self) -> Result<bool, Self::Error> {
        embedded_io_async::WriteReady::write_ready(&mut self.inner)
    }
}

impl embedded_io_async::Write for BufferedUartPort {
    async fn write(&mut self, buf: &[u8]) -> Result<usize, Self::Error> {
        embedded_io_async::Write::write(&mut self.inner, buf).await
    }
}
