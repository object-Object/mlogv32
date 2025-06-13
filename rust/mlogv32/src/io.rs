use core::{arch::asm, hint, slice};

use embassy_hal_internal::atomic_ring_buffer::RingBuffer;
use uart::{Data, FifoControl, LineStatus, Uart, address::MmioAddress};

pub use uart;

pub fn print_str(msg: &str) {
    for c in msg.chars() {
        print_char(c);
    }
}

pub fn print_char(c: char) {
    unsafe {
        asm!(
            ".insn i CUSTOM_0, 0, zero, {}, 1",
            in(reg) c as u32,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn print_flush() {
    unsafe {
        asm!(
            ".insn i CUSTOM_0, 0, zero, zero, 2",
            options(nomem, preserves_flags, nostack),
        );
    }
}

// TODO: create Peripherals struct?

const UART0_ADDRESS: usize = 0xf0000010;
const UART1_ADDRESS: usize = 0xf0000030;

pub struct UartPort {
    uart: Uart<MmioAddress, Data>,
    fifo_capacity: usize,
    fifo_len: usize,
}

impl UartPort {
    /// # Safety
    ///
    /// This function is unsafe because the caller must ensure that only one instance of each device exists at a time, as it represents a physical memory-mapped peripheral.
    pub unsafe fn new_uart0(fifo_capacity: usize) -> Self {
        unsafe { Self::new_with_address(UART0_ADDRESS as *mut u8, fifo_capacity) }
    }

    /// # Safety
    ///
    /// This function is unsafe because the caller must ensure that only one instance of each device exists at a time, as it represents a physical memory-mapped peripheral.
    pub unsafe fn new_uart1(fifo_capacity: usize) -> Self {
        unsafe { Self::new_with_address(UART1_ADDRESS as *mut u8, fifo_capacity) }
    }

    /// # Safety
    ///
    /// This function is unsafe because the caller must ensure that only one instance of each device exists at a time, as it represents a physical memory-mapped peripheral. The caller must also ensure that the fifo capacity is correct.
    unsafe fn new_with_address(base: *mut u8, fifo_capacity: usize) -> Self {
        Self {
            uart: unsafe { Uart::new(MmioAddress::new(base, 4)) },
            fifo_capacity,
            fifo_len: 0,
        }
    }

    pub fn init(&mut self) {
        self.uart.write_fifo_control(
            FifoControl::ENABLE | FifoControl::CLEAR_RX | FifoControl::CLEAR_TX,
        );
    }

    pub fn clear(&mut self) {
        self.uart
            .write_fifo_control(FifoControl::CLEAR_RX | FifoControl::CLEAR_TX);
    }

    pub fn uart_mut(&mut self) -> &mut Uart<MmioAddress, Data> {
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
            Some(self.uart.read_byte())
        } else {
            None
        }
    }

    pub fn has_data(&self) -> bool {
        self.uart
            .read_line_status()
            .contains(LineStatus::DATA_AVAILABLE)
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
        if self.uart.read_line_status().contains(LineStatus::THR_EMPTY) {
            self.fifo_len = 0
        }
        if self.fifo_len < self.fifo_capacity {
            self.uart.write_byte(byte);
            self.fifo_len += 1;
            true
        } else {
            false
        }
    }

    pub fn can_write(&self) -> bool {
        self.uart.read_line_status().contains(LineStatus::THR_EMPTY)
            || self.fifo_len < self.fifo_capacity
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

        if self
            .uart
            .read_line_status()
            .contains(LineStatus::OVERRUN_ERROR)
        {
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

        if self
            .uart
            .read_line_status()
            .contains(LineStatus::OVERRUN_ERROR)
        {
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
