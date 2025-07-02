from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Annotated

import yaml
from pydantic import AfterValidator, BaseModel, Field, field_validator

_relative_path_root_var = ContextVar[Path]("_relative_path_root_var")


@contextmanager
def relative_path_root(path: str | Path):
    token = _relative_path_root_var.set(Path(path))
    yield
    _relative_path_root_var.reset(token)


def _RelativePath_after(path: Path):
    return (_relative_path_root_var.get() / path).resolve()


type RelativePath = Annotated[Path, AfterValidator(_RelativePath_after)]


class BuildConfig(BaseModel):
    templates: Templates
    schematics: Schematics
    configs: RelativePath
    instructions: list[Instruction]

    class Templates(BaseModel):
        controller: RelativePath
        worker: RelativePath

    class Schematics(BaseModel):
        lookups: RelativePath
        ram: RelativePath

    class Instruction(BaseModel):
        label: str
        count: int = Field(default=1, ge=1)
        up_to: int | None = None

    @field_validator("instructions", mode="after")
    @classmethod
    def _resolve_instructions(cls, instructions: list[Instruction]):
        result = list[BuildConfig.Instruction]()
        address = 0

        for i, value in enumerate(instructions):
            if value.up_to is not None:
                value = value.model_copy()
                assert value.up_to is not None

                if value.up_to < address:
                    raise ValueError(
                        f"Instruction {i} is at address {address}, but up_to is {value.up_to}: {value}"
                    )

                value.count = value.up_to - address + 1

            result.append(value)
            address += value.count

        return result

    @classmethod
    def load(cls, path: str | Path):
        path = Path(path).resolve()

        with path.open("rb") as f:
            data = yaml.load(f, yaml.Loader)

        with relative_path_root(path.parent):
            return cls.model_validate(data)
