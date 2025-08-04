from typing import Any, TypedDict


class Labels(TypedDict, total=False):
    up: str
    left: str
    right: str
    down: str


class ConfigsYaml(TypedDict):
    template: str
    defaults: dict[str, Any]
    configs: dict[str, dict[str, Any]]


class ConfigArgs(TypedDict):
    UART_FIFO_CAPACITY: int
    DATA_ROM_ROWS: int
    MTIME_FREQUENCY: int

    MEMORY_X_OFFSET: int
    MEMORY_Y_OFFSET: int
    MEMORY_WIDTH: int
    PROGRAM_ROM_ROWS: int
    RAM_ROWS: int
    ICACHE_ROWS: int
