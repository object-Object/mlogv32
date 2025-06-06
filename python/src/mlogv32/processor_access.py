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

    def flash(self, path: str | Path):
        path = Path(path)
        if not path.is_absolute():
            raise ValueError("Path must be absolute.")

        self._send_request(FlashRequest(path=path))
        return self._recv_response(SuccessResponse)

    def dump(
        self,
        path: str | Path,
        address: int | None = None,
        bytes: int | None = None,
    ):
        path = Path(path)
        if not path.is_absolute():
            raise ValueError("Path must be absolute.")

        self._send_request(DumpRequest(path=path, address=address, bytes=bytes))
        return self._recv_response(SuccessResponse)

    def start(self, wait: bool):
        self._send_request(StartRequest(wait=wait))
        return self._recv_response(SuccessResponse)

    def stop(self):
        self._send_request(StopRequest())
        return self._recv_response(SuccessResponse)

    def status(self):
        self._send_request(StatusRequest())
        return self._recv_response(StatusResponse)

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
    )


class FlashRequest(BaseModel):
    type: Literal["flash"] = "flash"
    path: Path


class DumpRequest(BaseModel):
    type: Literal["dump"] = "dump"
    path: Path
    address: int | None
    bytes: int | None


class StartRequest(BaseModel):
    type: Literal["start"] = "start"
    wait: bool


class StopRequest(BaseModel):
    type: Literal["stop"] = "stop"


class StatusRequest(BaseModel):
    type: Literal["status"] = "status"


type Request = Annotated[
    FlashRequest | DumpRequest | StartRequest | StopRequest | StatusRequest,
    Field(discriminator="type"),
]


class SuccessResponse(BaseModel):
    type: Literal["success"]
    message: str


class StatusResponse(BaseModel):
    type: Literal["status"]
    running: bool
    pc: int | None
    error_output: str


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
