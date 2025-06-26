from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated, Any, TypedDict, Unpack, cast

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from pymsch import Block, Content, ProcessorConfig, ProcessorLink, Schematic
from typer import Option, Typer

from mlogv32.utils.msch import BEContent

from .extensions import CommentStatement
from .filters import FILTERS
from .models import BuildConfig
from .parser import iter_labels, parse_mlog

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
    width: Annotated[int, Option("-w", "--width")] = 16,
    height: Annotated[int, Option("-h", "--height")] = 16,
    size: Annotated[int | None, Option("-s", "--size")] = None,
    output: Annotated[Path | None, Option("-o", "--output")] = None,
    cpu_only: bool = False,
):
    """Generate a CPU schematic."""

    if size:
        width = size
        height = size

    config = BuildConfig.load(yaml_path)

    worker_output = get_template_output_path(config.templates.worker)
    worker_code = render_template(config.templates.worker, worker_output)

    labels = dict(iter_labels(parse_mlog(worker_code)))

    controller_output = get_template_output_path(config.templates.controller)
    controller_code = render_template(
        config.templates.controller,
        controller_output,
        instructions=config.instructions,
        labels=labels,
    )

    lookups_schem = cast(
        Schematic,
        Schematic.read_file(str(config.schematics.lookups)),  # type: ignore
    )
    assert lookups_schem.get_dimensions() == (4, 4)

    ram_schem = cast(
        Schematic,
        Schematic.read_file(str(config.schematics.ram)),  # type: ignore
    )
    assert ram_schem.get_dimensions() == (1, 1)

    schem = Schematic()

    for x in lenrange(0, 16):
        for y in lenrange(0, 16):
            schem.add_block(simple_block(BEContent.TILE_LOGIC_DISPLAY, x, y))

    display_link = ProcessorLink(0, 0, "")

    schem.add_schem(lookups_schem, 0, 16)
    lookup_links = [ProcessorLink(x=i % 4, y=16 + i // 4, name="") for i in range(16)]

    add_label(schem, 4, 19, right="UART0, UART2", down="LABELS")
    schem.add_block(simple_block(Content.WORLD_CELL, 4, 18))
    schem.add_block(simple_block(Content.WORLD_CELL, 4, 17))
    add_label(schem, 4, 16, up="COSTS", right="UART1, UART3")

    labels_link = ProcessorLink(4, 18, "")
    costs_link = ProcessorLink(4, 17, "")

    uart_links = list[ProcessorLink]()
    for x in lenrange(5, 4, 2):
        for y in lenrange(18, -4, -2):
            schem.add_block(simple_block(Content.MEMORY_BANK, x, y))
            uart_links.append(ProcessorLink(x, y, ""))

    schem.add_block(simple_block(Content.MEMORY_CELL, 9, 19))
    schem.add_schem(ram_schem, 9, 18)
    schem.add_schem(ram_schem, 9, 17)
    schem.add_block(Block(Content.MICRO_PROCESSOR, 9, 16, ProcessorConfig("", []), 0))

    registers_link = ProcessorLink(9, 19, "")
    csrs_link = ProcessorLink(9, 18, "")
    incr_link = ProcessorLink(9, 17, "")
    config_link = ProcessorLink(9, 16, "")

    add_with_label(
        schem,
        simple_block(Content.MESSAGE, 11, 19),
        left="REGISTERS",
        right="ERROR_OUTPUT",
    )
    add_with_label(
        schem,
        Block(Content.SWITCH, 11, 18, False, 0),
        left="CSRS",
        right="POWER_SWITCH",
    )
    add_with_label(
        schem,
        Block(Content.SWITCH, 11, 17, False, 0),
        left="INCR",
        right="PAUSE_SWITCH",
    )
    add_with_label(
        schem,
        Block(Content.SWITCH, 11, 16, False, 0),
        left="CONFIG",
        right="SINGLE_STEP_SWITCH",
    )

    error_output_link = ProcessorLink(11, 19, "")
    power_switch_link = ProcessorLink(11, 18, "")
    pause_switch_link = ProcessorLink(11, 17, "")
    single_step_switch_link = ProcessorLink(11, 16, "")

    # hack
    if cpu_only:
        schem = Schematic()

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
                    costs_link,
                    csrs_link,
                    incr_link,
                    config_link,
                    error_output_link,
                    power_switch_link,
                    pause_switch_link,
                    single_step_switch_link,
                    display_link,
                    x=16,
                    y=0,
                ),
            ),
            rotation=0,
        )
    )

    controller_link = ProcessorLink(16, 0, "")

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
                            costs_link,
                            csrs_link,
                            incr_link,
                            config_link,
                            controller_link,
                            error_output_link,
                            single_step_switch_link,
                            display_link,
                            x=x,
                            y=y,
                        ),
                    ),
                    rotation=0,
                )
            )

    if output:
        schem.write_file(str(output))
    else:
        schem.write_clipboard()


def lenrange(start: int, length: int, step: int = 1):
    return range(start, start + length, step)


def simple_block(block: Content | BEContent, x: int, y: int):
    return Block(block, x, y, None, 0)


def relative_links(*links: ProcessorLink, x: int, y: int):
    return [ProcessorLink(link.x - x, link.y - y, link.name) for link in links]


class Labels(TypedDict, total=False):
    up: str
    left: str
    right: str
    down: str


def add_label(schem: Schematic, x: int, y: int, **labels: Unpack[Labels]):
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
    schem.add_block(
        Block(
            block=Content.MESSAGE,
            x=x,
            y=y,
            config=label,
            rotation=0,
        )
    )


def add_with_label(schem: Schematic, block: Block, **labels: Unpack[Labels]):
    add_label(schem, block.x - 1, block.y, **labels)
    schem.add_block(block)


def create_jinja_env(template_dir: Path):
    env = Environment(
        loader=FileSystemLoader(template_dir),
        line_statement_prefix="#%",
        line_comment_prefix="#%#",
        autoescape=False,
        lstrip_blocks=True,
        trim_blocks=True,
        undefined=StrictUndefined,
        extensions=[
            CommentStatement,
        ],
    )
    env.filters |= FILTERS
    return env


def render_template(path: Path, output: Path | None, **kwargs: Any):
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


class ConfigsYaml(TypedDict):
    template: str
    defaults: dict[str, Any]
    configs: dict[str, dict[str, Any]]


if __name__ == "__main__":
    app()
