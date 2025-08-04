from __future__ import annotations

import math
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Annotated, Any, Iterable, Iterator, Literal

import yaml
from pydantic import (
    AfterValidator,
    BaseModel,
    Field,
    SerializationInfo,
    WrapSerializer,
    field_validator,
)

from mlogv32.preprocessor.constants import CSRS

_relative_path_root_var = ContextVar[Path]("_relative_path_root_var")


@contextmanager
def relative_path_root(path: str | Path):
    token = _relative_path_root_var.set(Path(path))
    yield
    _relative_path_root_var.reset(token)


def _RelativePath_after(path: Path):
    return (_relative_path_root_var.get() / path).resolve()


type RelativePath = Annotated[Path, AfterValidator(_RelativePath_after)]

type CSRLocation = Literal["LABEL"] | str


class BuildConfig(BaseModel):
    templates: Templates
    schematics: Schematics
    configs: RelativePath
    inputs: dict[str, Any]
    instructions: list[Instruction]
    csrs: dict[str, CSR]

    class Templates(BaseModel):
        controller: RelativePath
        worker: RelativePath
        debugger: RelativePath
        display: RelativePath

    class Schematics(BaseModel):
        lookups: RelativePath
        ram: RelativePath
        sortkb: RelativePath

    class Instruction(BaseModel):
        label: str
        count: int = Field(default=1, ge=1)
        up_to: int | None = None
        align: int = Field(default=1, ge=1)
        address: int | None = None

    class CSR(BaseModel):
        read: CSRLocation
        write: CSRLocation | None = None
        mask: int = Field(default=0xFFFF_FFFF, ge=0, le=0xFFFF_FFFF)
        args: Iterable[Any] | None = None

    @field_validator("instructions", mode="after")
    @classmethod
    def _resolve_instructions(cls, instructions: list[Instruction]):
        result = list[BuildConfig.Instruction]()
        address = 0

        for i, value in enumerate(instructions):
            value = value.model_copy()
            if value.address is None:
                value.address = math.ceil(address / value.align) * value.align
            elif value.address < address:
                raise ValueError(
                    f"Instruction {i} is at address {value.address}, but the previous instruction was at address {address}"
                )
            address = value.address

            if value.up_to is not None:
                assert value.up_to is not None
                assert value.align == 1, "Align != 1 is not supported with up_to"

                if value.up_to < address:
                    raise ValueError(
                        f"Instruction {i} is at address {address}, but up_to is {value.up_to}: {value}"
                    )

                value.count = value.up_to - address + 1

            result.append(value)
            address += value.count * value.align

        return result

    @field_validator("csrs", mode="after")
    @classmethod
    def _resolve_csrs(cls, csrs: dict[str, CSR]):
        result = dict[str, BuildConfig.CSR]()

        for name, csr in cls._resolve_csr_args(csrs):
            csr = csr.model_copy()

            address = CSRS.get(name)
            if address is None:
                raise ValueError(f"Invalid CSR name: {name}")

            readonly = (address >> 10) & 0b11 == 0b11
            if readonly and csr.write is not None:
                raise ValueError(
                    f"Invalid CSR entry for {name}: CSR is read-only but write is set"
                )
            if not readonly and csr.write is None:
                raise ValueError(
                    f"Invalid CSR entry for {name}: CSR is read/write but write is not set"
                )

            if csr.read == "LABEL":
                csr.read = name
            if csr.write == "LABEL":
                csr.write = name

            result[name] = csr

        return result

    @classmethod
    def _resolve_csr_args(cls, csrs: dict[str, CSR]) -> Iterator[tuple[str, CSR]]:
        for name, csr in csrs.items():
            if csr.args is None:
                yield name, csr
                continue

            new_csr = csr.model_copy()
            new_csr.args = None
            for arg in csr.args:
                try:
                    yield name.format(arg), new_csr
                except Exception as e:
                    raise ValueError(f"Invalid CSR entry for {name}: {e}")

    @classmethod
    def load(cls, path: str | Path):
        path = Path(path).resolve()

        with path.open("rb") as f:
            data = yaml.load(f, yaml.Loader)

        with relative_path_root(path.parent):
            return cls.model_validate(data)


def _serialize_point(point: tuple[int, int], handler: Any, info: SerializationInfo):
    if info.context:
        x, y = point
        x_offset, y_offset = info.context["offsets"]
        return handler((x + x_offset, y + y_offset))
    return handler()


type MetaPoint2 = Annotated[
    tuple[int, int],
    WrapSerializer(_serialize_point),
]


class Metadata(BaseModel):
    uarts: list[MetaPoint2] = Field(default_factory=list)

    registers: MetaPoint2 | None = None
    csrs: MetaPoint2 | None = None
    config: MetaPoint2 | None = None
    uart_fifo_capacity: int | None = None

    error_output: MetaPoint2 | None = None
    power_switch: MetaPoint2 | None = None
    pause_switch: MetaPoint2 | None = None
    single_step_switch: MetaPoint2 | None = None

    cpu: MetaPoint2 | None = None
    cpu_width: int | None = None
    cpu_height: int | None = None

    memory: MetaPoint2 | None = None
    memory_width: int | None = None
    memory_height: int | None = None

    rom_processors: int | None = None
    ram_processors: int | None = None
    icache_processors: int | None = None

    mtime_frequency: int | None = None
