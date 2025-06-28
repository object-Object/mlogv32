from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Annotated, Any

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
    inputs: dict[str, Any]
    instructions: list[Instruction]

    class Templates(BaseModel):
        controller: RelativePath
        worker: RelativePath

    class Schematics(BaseModel):
        lookups: RelativePath
        ram: RelativePath

    class Instruction(BaseModel):
        label: str
        cost: int = Field(ge=0)

        @field_validator("cost", mode="before")
        @classmethod
        def _resolve_cost_math(cls, value: Any):
            if isinstance(value, str):
                return eval(value)  # CURSED
            return value

    @classmethod
    def load(cls, path: str | Path):
        path = Path(path).resolve()

        with path.open("rb") as f:
            data = yaml.load(f, yaml.Loader)

        with relative_path_root(path.parent):
            return cls.model_validate(data)
