from __future__ import annotations

import logging
import socket
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel as _BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    alias_generators,
)

logger = logging.getLogger(__name__)


class ProcessorAccess:
    def __init__(
        self,
        hostname: str,
        port: int,
        *,
        log_level: int = logging.DEBUG,
    ):
        self.hostname = hostname
        self.port = port
        self.log_level = log_level
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.socket.connect((self.hostname, self.port))

    def disconnect(self):
        self.socket.close()

    def flash(self, path: str | Path, *, absolute: bool = True):
        path = Path(path)
        if absolute and not path.is_absolute():
            raise ValueError("Path must be absolute.")

        self._send_request(FlashRequest(path=path, absolute=absolute))
        return self._recv_response(SuccessResponse)

    def dump(
        self,
        path: str | Path,
        address: int | None = None,
        data: int | None = None,
        *,
        absolute: bool = True,
    ):
        path = Path(path)
        if absolute and not path.is_absolute():
            raise ValueError("Path must be absolute.")

        self._send_request(
            DumpRequest(path=path, address=address, bytes=data, absolute=absolute)
        )
        return self._recv_response(SuccessResponse)

    def start(self, *, single_step: bool = False):
        self._send_request(StartRequest(single_step=single_step))
        return self._recv_response(SuccessResponse)

    def wait(self, *, stopped: bool, paused: bool):
        self._send_request(WaitRequest(stopped=stopped, paused=paused))
        return self._recv_response(SuccessResponse)

    def unpause(self):
        self._send_request(UnpauseRequest())
        return self._recv_response(SuccessResponse)

    def stop(self):
        self._send_request(StopRequest())
        return self._recv_response(SuccessResponse)

    def status(self):
        self._send_request(StatusRequest())
        return self._recv_response(StatusResponse)

    def serial(
        self,
        device: UartDevice,
        *,
        overrun: bool = False,
        stop_on_halt: bool = False,
        disconnect_on_halt: bool = False,
    ):
        self._send_request(
            SerialRequest(
                device=device,
                overrun=overrun,
                direction="both",
                stopOnHalt=stop_on_halt,
                disconnectOnHalt=disconnect_on_halt,
            )
        )
        return self.socket

    def _send_request(self, request: Request) -> None:
        message = request.model_dump_json() + "\n"
        logger.log(self.log_level, f"Sending request: {message.rstrip()}")
        self.socket.sendall(message.encode("utf-8"))

    def _recv_response[T](self, response_type: type[T]) -> T:
        with self.socket.makefile("r", encoding="utf-8") as f:
            line = f.readline()
        logger.log(self.log_level, f"Received response: {line.rstrip()}")
        match TypeAdapter(response_type | ErrorResponse).validate_json(line):
            case ErrorResponse() as e:
                raise ProcessorError(e)
            case response:
                return response

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_: Any):
        self.disconnect()
        return False  # propagate exceptions


class BaseModel(_BaseModel):
    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        validate_by_name=True,
        validate_by_alias=True,
        serialize_by_alias=True,
    )


class FlashRequest(BaseModel):
    type: Literal["flash"] = "flash"
    path: Path
    absolute: bool


class DumpRequest(BaseModel):
    type: Literal["dump"] = "dump"
    path: Path
    address: int | None
    bytes: int | None
    absolute: bool


class StartRequest(BaseModel):
    type: Literal["start"] = "start"
    single_step: bool


class WaitRequest(BaseModel):
    type: Literal["wait"] = "wait"
    stopped: bool
    paused: bool


class UnpauseRequest(BaseModel):
    type: Literal["unpause"] = "unpause"


class StopRequest(BaseModel):
    type: Literal["stop"] = "stop"


class StatusRequest(BaseModel):
    type: Literal["status"] = "status"


type UartDevice = Literal["uart0", "uart1", "uart2", "uart3"]


type UartDirection = Literal["both", "rx", "tx"]


class SerialRequest(BaseModel):
    type: Literal["serial"] = "serial"
    device: UartDevice
    overrun: bool
    direction: UartDirection
    stopOnHalt: bool
    disconnectOnHalt: bool


type Request = Annotated[
    FlashRequest
    | DumpRequest
    | StartRequest
    | WaitRequest
    | UnpauseRequest
    | StopRequest
    | StatusRequest
    | SerialRequest,
    Field(discriminator="type"),
]


class SuccessResponse(BaseModel):
    type: Literal["success"]
    message: str


class StatusResponse(BaseModel):
    type: Literal["status"]
    running: bool
    paused: bool
    state: str
    error_output: str
    pc: int | None
    instruction: int | None
    privilege_mode: int | None
    registers: list[int]
    mscratch: int
    mtvec: int
    mepc: int
    mcause: int
    mtval: int
    mstatus: int
    mip: int
    mie: int
    mcycle: int
    minstret: int
    mtime: int


class ErrorResponse(BaseModel):
    type: Literal["error"]
    message: str


type Response = Annotated[
    SuccessResponse | StatusResponse | ErrorResponse,
    Field(discriminator="type"),
]


class ProcessorError(RuntimeError):
    def __init__(self, response: ErrorResponse):
        super().__init__(response.message)
        self.response = response
