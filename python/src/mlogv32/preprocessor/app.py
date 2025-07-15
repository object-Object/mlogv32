from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated, Any, Iterable, Literal, Unpack, cast, overload

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from jinja2.ext import Extension
from pymsch import Block, Content, ProcessorConfig, ProcessorLink, Schematic
from typer import Option, Typer

from mlogv32.utils.msch import (
    BEContent,
    ProcessorConfigUTF8,
)

from .extensions import (
    CommentStatement,
    LineExpression,
    LineExpressionEnv,
    LocalVariables,
    LocalVariablesEnv,
)
from .filters import FILTERS, ram_var
from .models import BuildConfig
from .parser import (
    DirectiveError,
    Statement,
    check_unsaved_variables,
    iter_labels,
    parse_mlog,
)
from .types import ConfigArgs, ConfigsYaml, Labels

app = Typer(
    pretty_exceptions_show_locals=False,
)


@app.command(name="file")
def file_command(
    path: Path,
    output: Annotated[Path | None, Option("-o", "--output")] = None,
):
    """Preprocess a single .mlog.jinja file."""

    render_template(path.resolve(), output)


@app.command()
def labels(
    path: Path,
    output: Annotated[Path | None, Option("-o", "--output")] = None,
    filter_str: Annotated[str | None, Option("--filter")] = None,
):
    """Extract label addresses from a mlog file into set statements."""

    if filter_str:
        filter_re = re.compile(filter_str)
    else:
        filter_re = None

    with path.open("r", encoding="utf-8") as f:
        lines = parse_mlog(f.read())

    result = "\n".join(
        f"set {name} {line_num}"
        for name, line_num in iter_labels(lines)
        if not filter_re or filter_re.fullmatch(name)
    )

    if output:
        output.write_text(result, encoding="utf-8")
    else:
        print(result)


@app.command()
def configs(yaml_path: Path):
    """Generate CPU configs."""

    with yaml_path.open("rb") as f:
        data: ConfigsYaml = yaml.load(f, yaml.Loader)

    output_dir = yaml_path.parent
    env = create_jinja_env(output_dir)
    template = env.get_template(data["template"])

    for name, args in data["configs"].items():
        result = template.render(**(data["defaults"] | args))
        (output_dir / name).with_suffix(".mlog").write_text(result, "utf-8")


@app.command()
def build(
    yaml_path: Path,
    cpu_config_name: Annotated[str | None, Option("-c", "--config")] = None,
    width: Annotated[int, Option("-w", "--width")] = 16,
    height: Annotated[int, Option("-h", "--height")] = 16,
    size: Annotated[int | None, Option("-s", "--size")] = None,
    output: Annotated[Path | None, Option("-o", "--output")] = None,
    bin_path: Annotated[Path | None, Option("--bin")] = None,
    include_all: Annotated[bool, Option("--all")] = False,
    include_cpu: Annotated[bool, Option("--cpu")] = False,
    include_peripherals: Annotated[bool, Option("--peripherals")] = False,
    include_memory: Annotated[bool, Option("--memory")] = False,
    include_debugger: Annotated[bool, Option("--debugger")] = False,
    include_keyboard: Annotated[bool, Option("--keyboard/--no-keyboard")] = True,
):
    """Generate a CPU schematic.

    Memory configuration format (--config):

    - config_name (see src/config/configs.yaml)

    - program_rom_rows,ram_rows[,icache_rows[,memory_width[,x_offset[,data_rom_rows]]]]

    - rom=program_rom_rows,ram=ram_rows[,icache=icache_rows][,width=memory_width][,x_offset=x_offset][,drom=data_rom_rows]

    Defaults:

    - data_rom_rows: 0

    - icache_rows: rom + ram

    - memory_width: 32

    - x_offset: -9

    Examples:

    - riscv-arch-test

    - 1,1,1,32

    - 4,4

    - rom=2,ram=12,icache=2,width=16

    - rom=2,drom=8,ram=2,icache=4
    """

    if size:
        width = size
        height = size

    if include_keyboard and height > 16:
        raise ValueError(
            f"Maximum height is 16 if keyboard is enabled, but got {height}"
        )

    if include_all:
        include_cpu = True
        include_peripherals = True
        include_memory = True
        include_debugger = True

    config = BuildConfig.load(yaml_path)

    if cpu_config_name:
        with config.configs.open("rb") as f:
            cpu_configs: ConfigsYaml = yaml.load(f, yaml.Loader)

        if config_args := cpu_configs["configs"].get(cpu_config_name):
            config_args = cpu_configs["defaults"] | config_args

            configs(config.configs)

            config_code = (
                (config.configs.parent / cpu_config_name)
                .with_suffix(".mlog")
                .read_text("utf-8")
            )
        else:
            config_args = parse_config_str(cpu_config_name)
            if not config_args:
                raise KeyError(f"Invalid config: {cpu_config_name}")

            config_code = render_template(
                config.configs.parent / cpu_configs["template"],
                yaml_path.parent / "generated_config.mlog",
                **config_args,
            )
    else:
        if include_memory:
            raise ValueError(
                "--config is required if generating memory, but not supplied"
            )
        config_args = {}
        config_code = ""

    @overload
    def _render_template(
        template: Path,
        extensions: Iterable[type[Extension] | str] = (),
        *,
        force: Literal[True],
        **kwargs: Any,
    ) -> tuple[str, Environment, Path]: ...

    @overload
    def _render_template(
        template: Path,
        extensions: Iterable[type[Extension] | str] = (),
        *,
        force: Literal[False] = False,
        **kwargs: Any,
    ) -> tuple[str, Environment | None, Path | None]: ...

    def _render_template(
        template: Path,
        extensions: Iterable[type[Extension] | str] = (),
        *,
        force: bool = False,
        **kwargs: Any,
    ) -> tuple[str, Environment | None, Path | None]:
        if template.suffix == ".mlog" and not force:
            return template.read_text("utf-8"), None, None

        template_output = get_template_output_path(template)
        template_env = create_jinja_env(template.parent, extensions)
        rendered = render_template(
            template,
            template_output,
            template_env,
            **kwargs,
        )
        return rendered, template_env, template_output

    # preprocess and check worker

    variable_0_to_page_offset = list[str]()
    page_0 = ram_var(0)
    page_1 = ram_var(0x1000 // 4)
    page_2 = ram_var(0x2000 // 4)
    page_3 = ram_var(0x3000 // 4)
    for i in range(128):
        var = chr(i) + page_0[1]
        if i < 32 or var < page_1:
            value = "0"
        elif var < page_2:
            value = "1"
        elif var < page_3:
            value = "2"
        else:
            value = "3"
        variable_0_to_page_offset.append(value)

    worker_code, worker_env, worker_output = _render_template(
        config.templates.worker,
        [LocalVariables],
        force=True,
        VARIABLE_0_TO_PAGE_OFFSET="".join(variable_0_to_page_offset),
    )

    i = LocalVariablesEnv.of(worker_env).largest_local_variable
    print(f"Local variable count: {i}")

    worker_ast = parse_mlog(worker_code)

    check_unsaved_variables(worker_ast)
    print(
        f"""\
Code size:
  Instructions: {len(list(n for n in worker_ast if isinstance(n, Statement)))} / 1000
  Bytes: {len(worker_code.encode())} / {1024 * 100}"""
    )

    try:
        worker_labels = dict(iter_labels(worker_ast))
    except DirectiveError as e:
        e.add_note(f"{worker_output}:{e.token.line}")
        raise

    # preprocess controller

    controller_code, _, _ = _render_template(
        config.templates.controller,
        [LocalVariables],
        force=True,
        instructions=config.instructions,
        csrs=config.csrs,
        labels=worker_labels,
        VARIABLE_0_TO_PAGE_OFFSET="".join(variable_0_to_page_offset),
    )

    # preprocess other code snippets

    debugger_code, _, _ = _render_template(config.templates.debugger)

    display_code, _, _ = _render_template(config.templates.display)

    # load schematics

    lookups_schem = Schematic.read_file(str(config.schematics.lookups))
    assert lookups_schem.get_dimensions() == (4, 4)

    ram_schem = Schematic.read_file(str(config.schematics.ram))
    assert ram_schem.get_dimensions() == (1, 1)

    sortkb_schem = Schematic.read_file(str(config.schematics.sortkb))
    assert sortkb_schem.get_dimensions() == (5, 4)

    # begin generating output schematic

    schem = Schematic()

    @overload
    def add_peripheral(block: Block) -> None: ...

    @overload
    def add_peripheral(block: Schematic, x: int, y: int) -> None: ...

    def add_peripheral(block: Block | Schematic, x: int = 0, y: int = 0):
        if not include_peripherals:
            return
        match block:
            case Block():
                schem.add_block(block)
            case Schematic():
                schem.add_schem(block, x, y)

    def add_label(x: int, y: int, **labels: Unpack[Labels]):
        label = "\n".join(
            template.format(label)
            for key, template in [
                ("up", "{} ⇧"),
                ("left", "⇦ {}"),
                ("right", "{} ⇨"),
                ("down", "{} ⇩"),
            ]
            if (label := labels.get(key))
        )
        add_peripheral(
            Block(
                block=Content.MESSAGE,
                x=x,
                y=y,
                config=label,
                rotation=0,
            )
        )

    def add_with_label(block: Block, **labels: Unpack[Labels]):
        add_label(block.x - 1, block.y, **labels)
        add_peripheral(block)

    # peripherals

    for x in lenrange(0, 16):
        for y in lenrange(0, 16):
            add_peripheral(simple_block(BEContent.TILE_LOGIC_DISPLAY, x, y))

    display_link = ProcessorLink(0, 0, "")

    add_peripheral(lookups_schem, 0, 16)
    lookup_links = [
        ProcessorLink(x=i % 4, y=16 + i // 4, name=f"processor{i + 1}")
        for i in range(16)
    ]

    add_label(4, 19, right="UART0, UART2", down="LABELS")
    add_peripheral(simple_block(Content.WORLD_CELL, 4, 18))
    add_peripheral(ram_schem, 4, 17)
    add_label(4, 16, up="CSR_LABELS", right="UART1, UART3")

    labels_link = ProcessorLink(4, 18, "")
    csr_labels_link = ProcessorLink(4, 17, "processor20")

    uart_links = list[ProcessorLink]()
    for x in lenrange(5, 4, 2):
        for y in lenrange(18, -4, -2):
            add_peripheral(simple_block(Content.MEMORY_BANK, x, y))
            uart_links.append(ProcessorLink(x, y, ""))

    add_peripheral(simple_block(Content.MEMORY_CELL, 9, 19))
    add_peripheral(ram_schem, 9, 18)
    add_peripheral(ram_schem, 9, 17)
    add_peripheral(
        Block(Content.MICRO_PROCESSOR, 9, 16, ProcessorConfig(config_code, []), 0)
    )

    registers_link = ProcessorLink(9, 19, "cell1")
    csrs_link = ProcessorLink(9, 18, "")
    incr_link = ProcessorLink(9, 17, "")
    config_link = ProcessorLink(9, 16, "")

    add_with_label(
        simple_block(Content.MESSAGE, 11, 19),
        left="REGISTERS",
        right="ERROR_OUTPUT",
    )
    add_with_label(
        Block(Content.SWITCH, 11, 18, False, 0),
        left="CSRS",
        right="POWER_SWITCH",
    )
    add_with_label(
        Block(Content.SWITCH, 11, 17, False, 0),
        left="INCR",
        right="PAUSE_SWITCH",
    )
    add_with_label(
        Block(Content.SWITCH, 11, 16, False, 0),
        left="CONFIG",
        right="SINGLE_STEP_SWITCH",
    )

    error_output_link = ProcessorLink(11, 19, "")
    power_switch_link = ProcessorLink(11, 18, "")
    pause_switch_link = ProcessorLink(11, 17, "")
    single_step_switch_link = ProcessorLink(11, 16, "")

    add_peripheral(ram_schem, 13, 16)
    add_peripheral(ram_schem, 12, 17)
    add_peripheral(ram_schem, 13, 17)
    add_with_label(
        Block(Content.SWITCH, 13, 18, False, 0),
        right="UART0 -> DISPLAY",
    )

    add_peripheral(
        Block(
            block=Content.WORLD_PROCESSOR,
            x=12,
            y=16,
            config=ProcessorConfig(
                code=display_code,
                links=relative_links(
                    *lookup_links,
                    ProcessorLink(13, 16, "processor17"),  # BUFFER
                    ProcessorLink(12, 17, "processor18"),  # INCR (display)
                    ProcessorLink(13, 17, "processor19"),  # DECR
                    config_link,
                    ProcessorLink(13, 18, "switch1"),  # DISPLAY_POWER
                    power_switch_link,
                    uart_links[0],
                    display_link,
                    x=12,
                    y=16,
                ),
            ),
            rotation=0,
        )
    )

    add_peripheral(sortkb_schem, 14, 16)

    # CPU

    controller_link = ProcessorLink(16, 0, "")

    if include_cpu:
        schem.add_block(
            Block(
                block=Content.WORLD_PROCESSOR,
                x=16,
                y=0,
                config=ProcessorConfig(
                    code=controller_code,
                    links=relative_links(
                        *lookup_links,
                        *uart_links,
                        registers_link,
                        labels_link,
                        csrs_link,
                        incr_link,
                        config_link,
                        csr_labels_link,
                        error_output_link,
                        power_switch_link,
                        pause_switch_link,
                        single_step_switch_link,
                        x=16,
                        y=0,
                    ),
                ),
                rotation=0,
            )
        )

        for x in lenrange(16, width):
            for y in lenrange(0, height):
                # controller
                if x == 16 and y == 0:
                    continue

                schem.add_block(
                    Block(
                        block=Content.WORLD_PROCESSOR,
                        x=x,
                        y=y,
                        config=ProcessorConfig(
                            code=worker_code,
                            links=relative_links(
                                *lookup_links,
                                *uart_links,
                                registers_link,
                                labels_link,
                                csrs_link,
                                incr_link,
                                config_link,
                                csr_labels_link,
                                controller_link,
                                error_output_link,
                                x=x,
                                y=y,
                            ),
                        ),
                        rotation=0,
                    )
                )

    # memory
    if include_memory:
        i = 0
        if bin_path:
            data = bin_path.read_bytes()
            if len(data) % 4 != 0:
                print("[WARNING] Bin is not aligned to 4 bytes, appending zeros.")
                data += bytes([0, 0, 0, 0])[: len(data) % 4]
        else:
            data = bytes()

        base_y = config_link.y + config_args["MEMORY_Y_OFFSET"]
        for y in lenrange(
            0,
            config_args["PROGRAM_ROM_ROWS"]
            + config_args["DATA_ROM_ROWS"]
            + config_args["RAM_ROWS"]
            + config_args["ICACHE_ROWS"],
        ):
            for x in lenrange(
                config_link.x + config_args["MEMORY_X_OFFSET"],
                config_args["MEMORY_WIDTH"],
            ):
                if y < config_args["PROGRAM_ROM_ROWS"] + config_args["DATA_ROM_ROWS"]:
                    if i < len(data):
                        payload = "".join(chr(174 + c) for c in data[i : i + 16384])
                        i += 16384
                    else:
                        payload = ""

                    schem.add_block(
                        Block(
                            block=Content.MICRO_PROCESSOR,
                            x=x,
                            y=base_y + y,
                            config=ProcessorConfigUTF8(
                                code=f'set v "{payload}"; stop',
                                links=[],
                            ).compress(),
                            rotation=0,
                        )
                    )
                else:
                    schem.add_schem(ram_schem, x, base_y + y)

        if i < len(data):
            print(
                f"[WARNING] Bin is too large to fit into the generated ROM ({len(data) - i} bytes overflowed)."
            )

    # debugger

    if include_debugger:
        for x in lenrange(-18, 16):
            for y in lenrange(0, 16):
                schem.add_block(simple_block(BEContent.TILE_LOGIC_DISPLAY, x, y))

        schem.add_block(Block(Content.SWITCH, -2, 1, True, 0))

        schem.add_block(
            Block(
                block=Content.WORLD_PROCESSOR,
                x=-2,
                y=0,
                config=ProcessorConfig(
                    code=debugger_code,
                    links=relative_links(
                        *lookup_links,
                        *uart_links,
                        controller_link,
                        csrs_link,
                        registers_link,
                        ProcessorLink(-3, 0, ""),  # debugger display
                        ProcessorLink(-2, 1, ""),  # debugger power
                        x=-2,
                        y=0,
                    ),
                ),
                rotation=0,
            )
        )

    if schem.tiles:
        w, h = schem.get_dimensions()
        print(f"Schematic size: {w}x{h}")
        if output:
            print(f"Writing schematic to file: {output}")
            schem.write_file(str(output))
        else:
            print("Copying schematic to clipboard.")
            schem.write_clipboard()


def parse_config_str(config: str) -> ConfigArgs | None:
    items = config.split(",")
    if not (2 <= len(items) <= 4):
        return None

    inputs = dict[str, int]()

    for item, default_key in zip(
        items, ["rom", "ram", "icache", "width", "x_offset", "drom"]
    ):
        if "=" not in item:
            key = default_key
            value = item
        else:
            key, value = item.split("=", 1)

        try:
            inputs[key] = int(value, base=0)
        except ValueError:
            return None

    if "rom" not in inputs or "ram" not in inputs:
        return None

    if "icache" not in inputs:
        inputs["icache"] = inputs["rom"] + inputs["ram"]

    if "width" not in inputs:
        inputs["width"] = 32

    if "x_offset" not in inputs:
        inputs["x_offset"] = -9

    if "drom" not in inputs:
        inputs["drom"] = 0

    rows = inputs["rom"] + inputs["drom"] + inputs["ram"] + inputs["icache"]

    return ConfigArgs(
        UART_FIFO_CAPACITY=253,
        MEMORY_X_OFFSET=inputs["x_offset"],
        MEMORY_Y_OFFSET=-16 - rows,
        MEMORY_WIDTH=inputs["width"],
        PROGRAM_ROM_ROWS=inputs["rom"],
        DATA_ROM_ROWS=inputs["drom"],
        RAM_ROWS=inputs["ram"],
        ICACHE_ROWS=inputs["icache"],
    )


def lenrange(start: int, length: int, step: int = 1):
    return range(start, start + length, step)


def simple_block(block: Content | BEContent, x: int, y: int):
    # lie
    return Block(cast(Content, block), x, y, None, 0)


def relative_links(*links: ProcessorLink, x: int, y: int):
    return [ProcessorLink(link.x - x, link.y - y, link.name) for link in links]


def create_jinja_env(
    template_dir: Path,
    extensions: Iterable[type[Extension] | str] = (),
):
    env = Environment(
        loader=FileSystemLoader(template_dir),
        line_statement_prefix="#%",
        line_comment_prefix="#%#",
        autoescape=False,
        lstrip_blocks=True,
        trim_blocks=True,
        undefined=StrictUndefined,
        extensions=[
            "jinja2.ext.do",
            CommentStatement,
            LineExpression,
            *extensions,
        ],
    )
    LineExpressionEnv.extend(
        env,
        line_expression_prefix="#{",
    )
    env.filters |= FILTERS
    return env


def render_template(
    path: Path,
    output: Path | None,
    env: Environment | None = None,
    **kwargs: Any,
):
    if env is None:
        env = create_jinja_env(path.parent)
    template = env.get_template(path.name)
    result = template.render(**kwargs)

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(result, "utf-8")
    else:
        print(result)

    return result


def get_template_output_path(path: Path):
    if path.suffix != ".jinja":
        raise ValueError(f"Expected .jinja suffix, but got {path.suffix}: {path}")
    return path.with_suffix("")


if __name__ == "__main__":
    app()
