import itertools
from enum import StrEnum
from pathlib import Path
from typing import Annotated

from pymsch import Block, Content, ProcessorConfig, Schematic
from typer import Option, Typer

VARIABLE_NAME_CHARS = [
    chr(i) for i in range(33, 127) if chr(i) not in "\"#'0123456789;@\\"
]

VARIABLE_NAME_CHARS_MLOGV32 = VARIABLE_NAME_CHARS[:64]


class VariableFormat(StrEnum):
    mlogv32 = "mlogv32"
    min = "min"
    dec = "dec"
    hex = "hex"

    def iter_variables(self):
        match self:
            case VariableFormat.mlogv32:
                for c1 in VARIABLE_NAME_CHARS_MLOGV32:
                    for c2 in VARIABLE_NAME_CHARS_MLOGV32:
                        yield c1 + c2

            case VariableFormat.min:
                for c1 in VARIABLE_NAME_CHARS:
                    for c2 in VARIABLE_NAME_CHARS:
                        yield c1 + c2

            case VariableFormat.dec:
                for i in itertools.count():
                    yield f"v{i}"

            case VariableFormat.hex:
                # only prepend an underscore if we need to
                # otherwise we hit the save size limit with 4096 vars
                for i in itertools.count():
                    variable = f"{i:x}"
                    if variable[0].isdigit():
                        yield f"_{variable}"
                    else:
                        yield variable

    def get_variable(self, index: int):
        for i, variable in enumerate(self.iter_variables()):
            if i == index:
                return variable
        raise AssertionError


app = Typer()


@app.command()
def lookup(
    address_str: str,
    ram_size: Annotated[int, Option(min=1)] = 4096,
    ram_width: int = 128,
    variable_format: Annotated[
        VariableFormat,
        Option("-f", "--format"),
    ] = VariableFormat.mlogv32,
    base_x: Annotated[int, Option("-x", "--base-x")] = 1,
    base_y: Annotated[int, Option("-y", "--base-y")] = 1,
):
    address = int(address_str, base=0)

    word_address = address // 4

    ram_index = word_address // ram_size
    ram_x = ram_index % ram_width + base_x
    ram_y = ram_index // ram_width + base_y

    variable_index = word_address % ram_size
    variable = variable_format.get_variable(variable_index)

    print(
        f'Address {hex(address)} is at processor {ram_index} ({ram_x}, {ram_y}) in variable "{variable}".'
    )


@app.command()
def variables(
    indices: list[str],
    ram_size: Annotated[int, Option(min=1)] = 4096,
    variable_format: Annotated[
        VariableFormat,
        Option("-f", "--format"),
    ] = VariableFormat.mlogv32,
):
    for index_str in indices:
        index = int(index_str, base=0)
        if index >= ram_size:
            variable = "(out of range)"
        else:
            variable = variable_format.get_variable(index)
        print(f"{index_str} -> {variable}")


@app.command()
def build(
    ram_size: Annotated[int, Option(min=1)] = 4096,
    lookup_width: Annotated[int, Option(min=1)] = 4,
    variable_format: Annotated[
        VariableFormat,
        Option("-f", "--format"),
    ] = VariableFormat.mlogv32,
    out: Path = Path("schematics"),
):
    if ram_size > 726 * 6:
        print(f"WARNING: RAM proc sizes over {726 * 6} may fail to save!")

    lookup_procs, ram_proc = generate_code(ram_size, variable_format)

    out.mkdir(parents=True, exist_ok=True)

    schem1 = Schematic()
    schem1.set_tag("name", "lookup_procs")
    for i, code in enumerate(lookup_procs):
        schem1.add_block(
            Block(
                Content.MICRO_PROCESSOR,
                x=i % lookup_width,
                y=i // lookup_width,
                config=ProcessorConfig(code=code, links=[]),
                rotation=0,
            )
        )
    schem1.write_file(str(out / "lookup_procs.msch"))

    schem2 = Schematic()
    schem2.set_tag("name", "ram_proc")
    schem2.add_block(
        Block(
            Content.MICRO_PROCESSOR,
            x=0,
            y=0,
            config=ProcessorConfig(code=ram_proc, links=[]),
            rotation=0,
        )
    )
    schem2.write_file(str(out / "ram_proc.msch"))

    (out / "ram_proc.mlog").write_text(ram_proc, "utf-8")

    w, h = schem1.get_dimensions()
    print(
        f"Generated {len(lookup_procs)} lookup tables ({w}x{h}) for {ram_size} variables using {min(len(BLOCK_IDS), ram_size)} block ids."
    )


def generate_code(ram_size: int, variable_format: VariableFormat):
    done = False

    lookup_procs = list[str]()
    lookup_proc = list[str]()

    ram_proc = list[str]()
    ram_proc_line = list[str]()

    for variable in variable_format.iter_variables():
        ram_proc_line.append(variable)
        remaining_space = ram_size - len(ram_proc) * 6
        if remaining_space == len(ram_proc_line):
            done = True
            if remaining_space > 0:
                ram_proc.append(
                    "draw triangle "
                    + " ".join(
                        ram_proc_line + ram_proc_line[-1:] * (6 - len(ram_proc_line))
                    )
                )
        elif len(ram_proc_line) == 6:
            ram_proc.append("draw triangle " + " ".join(ram_proc_line))
            ram_proc_line.clear()

        block_id = BLOCK_IDS[len(lookup_proc)]
        lookup_proc.append(f'set {block_id} "{variable}"')
        if len(lookup_proc) == len(BLOCK_IDS) or done:
            lines = [
                'set _type "lookup"',
                f"set _index {len(lookup_procs)}",
                *lookup_proc,
                "stop",
            ]
            lookup_procs.append("\n".join(lines))
            lookup_proc.clear()

        if done:
            return lookup_procs, "\n".join(["stop"] + ram_proc)

    raise ValueError("Ran out of variable names!")


BLOCK_IDS = [
    "graphite-press",
    "multi-press",
    "silicon-smelter",
    "silicon-crucible",
    "kiln",
    "plastanium-compressor",
    "phase-weaver",
    "cryofluid-mixer",
    "pyratite-mixer",
    "blast-mixer",
    "melter",
    "separator",
    "disassembler",
    "spore-press",
    "pulverizer",
    "coal-centrifuge",
    "incinerator",
    "copper-wall",
    "copper-wall-large",
    "titanium-wall",
    "titanium-wall-large",
    "plastanium-wall",
    "plastanium-wall-large",
    "thorium-wall",
    "thorium-wall-large",
    "phase-wall",
    "phase-wall-large",
    "surge-wall",
    "surge-wall-large",
    "door",
    "door-large",
    "scrap-wall",
    "scrap-wall-large",
    "scrap-wall-huge",
    "scrap-wall-gigantic",
    "mender",
    "mend-projector",
    "overdrive-projector",
    "overdrive-dome",
    "force-projector",
    "shock-mine",
    "conveyor",
    "titanium-conveyor",
    "plastanium-conveyor",
    "armored-conveyor",
    "junction",
    "bridge-conveyor",
    "phase-conveyor",
    "sorter",
    "inverted-sorter",
    "router",
    "distributor",
    "overflow-gate",
    "underflow-gate",
    "mass-driver",
    "duct",
    "duct-router",
    "duct-bridge",
    "mechanical-pump",
    "rotary-pump",
    "conduit",
    "pulse-conduit",
    "plated-conduit",
    "liquid-router",
    "liquid-tank",
    "liquid-junction",
    "bridge-conduit",
    "phase-conduit",
    "power-node",
    "power-node-large",
    "surge-tower",
    "diode",
    "battery",
    "battery-large",
    "combustion-generator",
    "thermal-generator",
    "steam-generator",
    "differential-generator",
    "rtg-generator",
    "solar-panel",
    "solar-panel-large",
    "thorium-reactor",
    "impact-reactor",
    "mechanical-drill",
    "pneumatic-drill",
    "laser-drill",
    "blast-drill",
    "water-extractor",
    "cultivator",
    "oil-extractor",
    "core-shard",
    "core-foundation",
    "core-nucleus",
    "vault",
    "container",
    "unloader",
    "duo",
    "scatter",
    "scorch",
    "hail",
    "wave",
    "lancer",
    "arc",
    "parallax",
    "swarmer",
    "salvo",
    "segment",
    "tsunami",
    "fuse",
    "ripple",
    "cyclone",
    "foreshadow",
    "spectre",
    "meltdown",
    "command-center",
    "ground-factory",
    "air-factory",
    "naval-factory",
    "additive-reconstructor",
    "multiplicative-reconstructor",
    "exponential-reconstructor",
    "tetrative-reconstructor",
    "repair-point",
    "repair-turret",
    "payload-conveyor",
    "payload-router",
    "power-source",
    "power-void",
    "item-source",
    "item-void",
    "liquid-source",
    "liquid-void",
    "payload-void",
    "payload-source",
    "illuminator",
    "launch-pad",
    "interplanetary-accelerator",
    "message",
    "switch",
    "micro-processor",
    "logic-processor",
    "hyper-processor",
    "memory-cell",
    "memory-bank",
    "logic-display",
    "large-logic-display",
    "liquid-container",
    "deconstructor",
    "constructor",
    "thruster",
    "large-constructor",
    "payload-loader",
    "payload-unloader",
    "silicon-arc-furnace",
    "cliff-crusher",
    "plasma-bore",
    "reinforced-liquid-junction",
    "breach",
    "core-bastion",
    "turbine-condenser",
    "beam-node",
    "beam-tower",
    "build-tower",
    "impact-drill",
    "carbide-crucible",
    "surge-conveyor",
    "duct-unloader",
    "surge-router",
    "reinforced-conduit",
    "reinforced-liquid-router",
    "reinforced-liquid-container",
    "reinforced-liquid-tank",
    "reinforced-bridge-conduit",
    "core-citadel",
    "core-acropolis",
    "heat-reactor",
    "impulse-pump",
    "reinforced-pump",
    "electrolyzer",
    "oxidation-chamber",
    "surge-smelter",
    "surge-crucible",
    "overflow-duct",
    "large-plasma-bore",
    "cyanogen-synthesizer",
    "slag-centrifuge",
    "electric-heater",
    "slag-incinerator",
    "phase-synthesizer",
    "sublimate",
    "reinforced-container",
    "reinforced-vault",
    "atmospheric-concentrator",
    "unit-cargo-loader",
    "unit-cargo-unload-point",
    "chemical-combustion-chamber",
    "pyrolysis-generator",
    "regen-projector",
    "titan",
    "small-deconstructor",
    "vent-condenser",
    "phase-heater",
    "heat-redirector",
    "tungsten-wall",
    "tungsten-wall-large",
    "tank-assembler",
    "beryllium-wall",
    "beryllium-wall-large",
    "eruption-drill",
    "ship-assembler",
    "mech-assembler",
    "shield-projector",
    "beam-link",
    "world-processor",
    "reinforced-payload-conveyor",
    "reinforced-payload-router",
    "disperse",
    "large-shield-projector",
    "payload-mass-driver",
    "world-cell",
    "carbide-wall",
    "carbide-wall-large",
    "tank-fabricator",
    "mech-fabricator",
    "ship-fabricator",
    "reinforced-surge-wall",
    "radar",
    "blast-door",
    "canvas",
    "armored-duct",
    "unit-repair-tower",
    "diffuse",
    "prime-refabricator",
    "basic-assembler-module",
    "reinforced-surge-wall-large",
    "tank-refabricator",
    "mech-refabricator",
    "ship-refabricator",
    "slag-heater",
    "afflict",
    "shielded-wall",
    "lustre",
    "scathe",
    "smite",
    "underflow-duct",
    "malign",
    "shockwave-tower",
    "heat-source",
    "flux-reactor",
    "neoplasia-reactor",
    "heat-router",
    "large-payload-mass-driver",
    "reinforced-message",
    "world-message",
    "world-switch",
    "small-heat-redirector",
    "large-cliff-crusher",
    "advanced-launch-pad",
    "landing-pad",
    "tile-logic-display",
]

if __name__ == "__main__":
    app()
