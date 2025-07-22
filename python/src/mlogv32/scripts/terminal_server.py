from __future__ import annotations

import collections
import socket
import threading
import time
from socketserver import BaseRequestHandler, ThreadingTCPServer
from typing import Annotated

from typer import Option, Typer

from mlogv32.processor_access import ProcessorAccess, UartDevice

shutdown = threading.Event()
from_processor = collections.deque[bytes]()
from_client = collections.deque[bytes]()
from_input = collections.deque[bytes]()


class TerminalServerHandler(BaseRequestHandler):
    request: socket.socket

    def handle(self) -> None:
        self.request.setblocking(False)
        while True:
            if shutdown.is_set():
                self.request.close()
                break

            try:
                if msg := self.request.recv(1024):
                    from_client.append(msg)
            except BlockingIOError:
                pass

            if from_processor:
                self.request.sendall(from_processor.popleft())

            time.sleep(0)


def processor_worker(
    host: str,
    port: int,
    device: UartDevice,
    server: ThreadingTCPServer,
):
    try:
        with ProcessorAccess(host, port) as processor:
            sock = processor.serial(
                device,
                stop_on_halt=False,
                disconnect_on_halt=False,
            )
            sock.setblocking(False)
            while True:
                if shutdown.is_set():
                    break

                try:
                    if msg := sock.recv(1024):
                        print(
                            msg.decode(errors="ignore"),
                            end="",
                            flush=True,
                        )
                        from_processor.append(msg)
                except BlockingIOError:
                    pass

                if from_client:
                    msg = from_client.popleft()
                    print(
                        msg.decode(errors="ignore"),
                        end="",
                        flush=True,
                    )
                    sock.sendall(msg)

                if from_input:
                    msg = from_input.popleft()
                    sock.sendall(msg)

                time.sleep(0)
    finally:
        server.shutdown()
        shutdown.set()


def input_worker(server: ThreadingTCPServer):
    try:
        while True:
            msg = input() + "\r"
            from_input.append(msg.encode())
    finally:
        server.shutdown()
        shutdown.set()


app = Typer()


@app.command()
def main(
    *,
    processor_host: str = "localhost",
    processor_port: int = 5000,
    device: Annotated[str, Option("-d", "--device")] = "uart0",
    listen_host: Annotated[str, Option("-h", "--listen-host")] = "0.0.0.0",
    listen_port: Annotated[int, Option("-p", "--listen-port")] = 5001,
):
    try:
        with ThreadingTCPServer(
            (listen_host, listen_port),
            TerminalServerHandler,
        ) as server:
            threading.Thread(
                target=processor_worker,
                args=(processor_host, processor_port, device, server),
            ).start()

            threading.Thread(
                target=input_worker,
                args=(server,),
                daemon=True,
            ).start()

            server.serve_forever()
    finally:
        shutdown.set()


if __name__ == "__main__":
    app()
