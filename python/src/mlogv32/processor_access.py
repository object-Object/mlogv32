from __future__ import annotations

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


class ProcessorAccess:
    def __init__(self, hostname: str, port: int):
        self.hostname = hostname
        self.port = port
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
        return self._recv_response()

    def dump(self, path: str | Path):
        path = Path(path)
        if not path.is_absolute():
            raise ValueError("Path must be absolute.")

        self._send_request(DumpRequest(path=path))
        return self._recv_response()

    def start(self, wait: bool):
        self._send_request(StartRequest(wait=wait))
        return self._recv_response()

    def stop(self):
        self._send_request(StopRequest())
        return self._recv_response()

    def _send_request(self, request: Request) -> None:
        message = request.model_dump_json() + "\n"
        self.socket.sendall(message.encode("utf-8"))

    def _recv_response(self) -> Response:
        with self.socket.makefile("r", encoding="utf-8") as f:
            line = f.readline()
        return response_ta.validate_json(line)

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


class StartRequest(BaseModel):
    type: Literal["start"] = "start"
    wait: bool


class StopRequest(BaseModel):
    type: Literal["stop"] = "stop"


type Request = Annotated[
    FlashRequest | DumpRequest | StartRequest | StopRequest,
    Field(discriminator="type"),
]


class SuccessResponse(BaseModel):
    type: Literal["success"]
    message: str


class ErrorResponse(BaseModel):
    type: Literal["error"]
    message: str


type Response = Annotated[
    SuccessResponse | ErrorResponse,
    Field(discriminator="type"),
]

response_ta = TypeAdapter[Response](Response)
