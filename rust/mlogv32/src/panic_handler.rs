use crate::halt;
use crate::io::{print_flush, print_str};
use core::panic::PanicInfo;

#[panic_handler]
fn panic(info: &PanicInfo) -> ! {
    let message = info.message().as_str();
    let location = info.location();

    if message.is_none() && location.is_none() {
        print_str("thread panicked");
    } else {
        print_str("thread panicked:");
        if let Some(message) = message {
            print_str("\n");
            print_str(message);
        }
        if let Some(location) = location {
            print_str("\n");
            print_str(location.file());
        }
    }

    print_flush();

    halt();
}
