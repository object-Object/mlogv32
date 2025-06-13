#![no_std]
#![no_main]
#![feature(impl_trait_in_assoc_type)]

use core::{cell::RefCell, panic::PanicInfo};

use embassy_net_ppp::Device;
use embassy_sync::blocking_mutex::CriticalSectionMutex;
use embassy_time::Duration;
use embedded_io::{ReadReady, Write};
use log::{Log, SetLoggerError};
use mlogv32::{
    io::{BufferedUartPort, UartPort},
    register,
};
use picoserve::{AppBuilder, AppRouter, make_static, routing::get};

#[panic_handler]
fn panic(info: &PanicInfo) -> ! {
    panic_persist::report_panic_info(info);
    mlogv32::reboot();
}

struct Logger {
    uart: CriticalSectionMutex<RefCell<UartPort>>,
}

impl Logger {
    fn init(&'static self) -> Result<(), SetLoggerError> {
        log::set_logger(self)?;
        log::set_max_level(log::LevelFilter::Info);
        Ok(())
    }
}

impl Log for Logger {
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

#[embassy_executor::task]
async fn ppp_task(mut runner: embassy_net_ppp::Runner<'static>, mut uart: BufferedUartPort) -> ! {
    loop {
        let config = embassy_net_ppp::Config {
            username: b"username",
            password: b"password",
        };

        log::info!("Starting PPP runner.");

        let e = runner
            .run(&mut uart, config, |status| {
                match status.address {
                    Some(addr) => log::info!("Address: {addr}"),
                    None => log::warn!("Address: <unknown>"),
                };
                match status.peer_address {
                    Some(addr) => log::info!("Peer: {addr}"),
                    None => log::warn!("Peer: <unknown>"),
                };
            })
            .await
            .unwrap_err();

        log::error!("PPP runner failed: {e:?}");
    }
}

#[embassy_executor::task]
async fn net_task(mut runner: embassy_net::Runner<'static, Device<'static>>) -> ! {
    runner.run().await
}

struct AppProps;

impl AppBuilder for AppProps {
    type PathRouter = impl picoserve::routing::PathRouter;

    fn build_app(self) -> picoserve::Router<Self::PathRouter> {
        picoserve::Router::new().route("/", get(|| async move { "Hello World" }))
    }
}

const WEB_TASK_POOL_SIZE: usize = 4;
const SOCKETS: usize = WEB_TASK_POOL_SIZE + 1; // one extra socket for DNS, apparently

#[embassy_executor::task(pool_size = WEB_TASK_POOL_SIZE)]
async fn web_task(
    id: usize,
    stack: embassy_net::Stack<'static>,
    app: &'static AppRouter<AppProps>,
    config: &'static picoserve::Config<Duration>,
) -> ! {
    let port = 8080;
    let mut tcp_rx_buffer = [0; 1024];
    let mut tcp_tx_buffer = [0; 1024];
    let mut http_buffer = [0; 2048];

    picoserve::listen_and_serve(
        id,
        app,
        config,
        stack,
        port,
        &mut tcp_rx_buffer,
        &mut tcp_tx_buffer,
        &mut http_buffer,
    )
    .await
}

#[embassy_executor::main]
async fn main(spawner: embassy_executor::Spawner) {
    unsafe { mlogv32_embassy::init_timer() };

    let mut log_port = unsafe { UartPort::new_uart0(253) };
    log_port.init();

    let logger = make_static!(
        Logger,
        Logger {
            uart: CriticalSectionMutex::new(RefCell::new(log_port))
        }
    );
    logger.init().unwrap();

    if let Some(panic_message) = panic_persist::get_panic_message_utf8() {
        log::error!("{}", panic_message.trim());
        log::error!("Halting.");
        mlogv32::halt();
    }

    log::info!("Initializing PPP.");

    let mut ppp_port = BufferedUartPort::new(
        unsafe { UartPort::new_uart1(253) },
        make_static!([u8; 1024], [0; 1024]),
    );

    ppp_port.init();

    // if the mlogv32-utils socket server is still trying to send us more data, keep clearing the port until it stops
    while let Ok(true) = ppp_port.read_ready() {
        ppp_port.clear();
        embassy_futures::yield_now().await;
    }

    let (ppp_device, ppp_runner) = embassy_net_ppp::new(make_static!(
        embassy_net_ppp::State<64, 64>,
        embassy_net_ppp::State::new()
    ));

    spawner.must_spawn(ppp_task(ppp_runner, ppp_port));

    log::info!("Initializing network stack.");

    let (stack, runner) = embassy_net::new(
        ppp_device,
        embassy_net::Config::ipv4_static(embassy_net::StaticConfigV4 {
            address: embassy_net::Ipv4Cidr::new(core::net::Ipv4Addr::new(192, 168, 7, 10), 24),
            gateway: None,
            dns_servers: Default::default(),
        }),
        make_static!(
            embassy_net::StackResources<SOCKETS>,
            embassy_net::StackResources::new()
        ),
        register::cycle::read64(), // TODO: there's probably a better way to get a random seed than this
    );

    spawner.must_spawn(net_task(runner));

    log::info!("Starting app.");

    let app = make_static!(AppRouter<AppProps>, AppProps.build_app());

    let config = make_static!(
        picoserve::Config<Duration>,
        picoserve::Config::new(picoserve::Timeouts {
            start_read_request: Some(Duration::from_secs(5)),
            persistent_start_read_request: Some(Duration::from_secs(1)),
            read_request: Some(Duration::from_secs(1)),
            write: Some(Duration::from_secs(1)),
        })
        .keep_connection_alive()
    );

    for id in 0..WEB_TASK_POOL_SIZE {
        spawner.must_spawn(web_task(id, stack, app, config));
    }
}
