// see: https://github.com/embassy-rs/ppproto/blob/bd16b3093fe2ededb4fd7662ed253d7bc6b39a9b/examples/src/bin/simple.rs

#![no_std]
#![no_main]

use mlogv32::io::UartPort;
use ppproto::Config;
use ppproto::pppos::{PPPoS, PPPoSAction};

#[mlogv32::entry]
fn main() -> ! {
    let mut log_port = unsafe { UartPort::new_uart0(253) };
    let mut ppp_port = unsafe { UartPort::new_uart1(253) };

    log_port.init();
    ppp_port.init();

    log_port.blocking_write(b"initializing ppp\n");

    let config = Config {
        username: b"username",
        password: b"password",
    };
    let mut ppp = PPPoS::new(config);
    ppp.open().unwrap();

    log_port.blocking_write(b"ppp opened\n");

    let mut rx_buf = [0; 2048];
    let mut tx_buf = [0; 2048];

    let mut read_buf = [0; 2048];
    let mut data: &[u8] = &[];

    loop {
        // Poll the ppp
        match ppp.poll(&mut tx_buf, &mut rx_buf) {
            PPPoSAction::None => {}
            PPPoSAction::Transmit(n) => ppp_port.blocking_write(&tx_buf[..n]),
            PPPoSAction::Received(range) => {
                let pkt = &mut rx_buf[range];
                log_port.blocking_write(b"received request\n");

                // Toy code to reply to pings with no error handling whatsoever.
                let header_len = (pkt[0] & 0x0f) as usize * 4;
                let proto = pkt[9];
                if proto == 1 {
                    // ICMP packet
                    let icmp_type = pkt[header_len];
                    let icmp_code = pkt[header_len + 1];

                    if icmp_type == 8 && icmp_code == 0 {
                        // ICMP Echo Request

                        // Transform to echo response
                        pkt[header_len] = 0;

                        // Fix checksum
                        pkt[header_len + 2] = 0;
                        pkt[header_len + 3] = 0;
                        let c = !checksum(&pkt[header_len..]);
                        pkt[header_len + 2..][..2].copy_from_slice(&c.to_be_bytes());

                        // Swap source and dest addressses
                        let mut src_addr = [0; 4];
                        let mut dst_addr = [0; 4];
                        src_addr.copy_from_slice(&pkt[12..16]);
                        dst_addr.copy_from_slice(&pkt[16..20]);
                        pkt[12..16].copy_from_slice(&dst_addr);
                        pkt[16..20].copy_from_slice(&src_addr);

                        // Send it!
                        let n = ppp.send(pkt, &mut tx_buf).unwrap();
                        ppp_port.blocking_write(&tx_buf[..n]);

                        log_port.blocking_write(b"replied to ping!\n");
                    }
                }
            }
        }

        // If we have no data, read some.
        if data.is_empty() {
            let n = ppp_port.read(&mut read_buf);
            data = &read_buf[..n];
        }

        // Consume some data, saving the rest for later
        let n = ppp.consume(data, &mut rx_buf);
        data = &data[n..];
    }
}

fn propagate_carries(word: u32) -> u16 {
    let sum = (word >> 16) + (word & 0xffff);
    ((sum >> 16) as u16) + (sum as u16)
}

/// Compute an RFC 1071 compliant checksum (without the final complement).
fn checksum(data: &[u8]) -> u16 {
    let mut accum = 0;

    for c in data.chunks(2) {
        let x = if c.len() == 2 {
            (c[0] as u32) << 8 | (c[1] as u32)
        } else {
            (c[0] as u32) << 8
        };

        accum += x;
    }

    propagate_carries(accum)
}
