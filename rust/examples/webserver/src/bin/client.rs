#![no_std]
#![no_main]
#![feature(impl_trait_in_assoc_type)]

use core::{cell::RefCell, panic::PanicInfo};

use embassy_net::{
    dns::DnsSocket,
    tcp::client::{TcpClient, TcpClientState},
};
use embassy_net_ppp::Device;
use embassy_sync::blocking_mutex::CriticalSectionMutex;
use embedded_io::ReadReady;
use mlogv32::{
    io::{BufferedUartPort, UartPort},
    register,
};
use picoserve::make_static;
use reqwless::{client::HttpClient, request::Method};
use webserver::UartLogger;

#[panic_handler]
fn panic(info: &PanicInfo) -> ! {
    panic_persist::report_panic_info(info);
    mlogv32::reboot();
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

const SOCKETS: usize = 2;

#[embassy_executor::main]
async fn main(spawner: embassy_executor::Spawner) {
    unsafe { mlogv32_embassy::init_timer() };

    let mut log_port = unsafe { UartPort::new_uart0(253) };
    log_port.init();

    let logger = make_static!(
        UartLogger,
        UartLogger {
            uart: CriticalSectionMutex::new(RefCell::new(log_port)),
            level: log::LevelFilter::Info,
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
            address: embassy_net::Ipv4Cidr::new(core::net::Ipv4Addr::new(192, 168, 7, 11), 24),
            gateway: None,
            dns_servers: Default::default(),
        }),
        make_static!(
            embassy_net::StackResources<SOCKETS>,
            embassy_net::StackResources::new()
        ),
        register::cycle::read64(),
    );

    spawner.must_spawn(net_task(runner));

    let url = "http://192.168.7.10:8080";
    log::info!("Sending GET request to {url}...");

    let tcp_client = TcpClient::new(
        stack,
        make_static!(TcpClientState::<1, 1024, 1024>, TcpClientState::new()),
    );

    let dns_socket = DnsSocket::new(stack);

    let mut client = HttpClient::new(&tcp_client, &dns_socket);

    let mut request = client.request(Method::GET, url).await.unwrap();

    let mut buffer = [0_u8; 1024];
    let response = request.send(&mut buffer).await.unwrap();

    let body = response.body().read_to_end().await.unwrap();

    log::info!("Response:\n{}", str::from_utf8(body).unwrap());

    mlogv32::halt();
}
