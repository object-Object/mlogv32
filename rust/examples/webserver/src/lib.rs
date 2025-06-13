#![no_std]

use core::cell::RefCell;

use embassy_sync::blocking_mutex::CriticalSectionMutex;
use embedded_io::Write;
use log::{LevelFilter, Log, SetLoggerError};
use mlogv32::io::UartPort;

pub struct UartLogger {
    pub uart: CriticalSectionMutex<RefCell<UartPort>>,
    pub level: LevelFilter,
}

impl UartLogger {
    pub fn init(&'static self) -> Result<(), SetLoggerError> {
        log::set_logger(self)?;
        log::set_max_level(self.level);
        Ok(())
    }
}

impl Log for UartLogger {
    fn enabled(&self, _metadata: &log::Metadata) -> bool {
        true
    }

    fn log(&self, record: &log::Record) {
        self.uart.lock(|uart| {
            writeln!(uart.borrow_mut(), "[{}] {}", record.level(), record.args()).unwrap();
        });
    }

    fn flush(&self) {}
}
