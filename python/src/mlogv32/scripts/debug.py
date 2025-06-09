import logging
from pathlib import Path
from typing import Annotated

from pydantic import TypeAdapter
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm
from typer import Option, Typer

from mlogv32.processor_access import ProcessorAccess, StatusResponse

logger = logging.getLogger(__name__)

app = Typer(
    pretty_exceptions_show_locals=False,
)

REGISTER_NAMES = [
    "zero",
    "ra",
    "sp",
    "gp",
    "tp",
    "t0",
    "t1",
    "t2",
    "s0/fp",
    "s1",
    "a0",
    "a1",
    "a2",
    "a3",
    "a4",
    "a5",
    "a6",
    "a7",
    "s2",
    "s3",
    "s4",
    "s5",
    "s6",
    "s7",
    "s8",
    "s9",
    "s10",
    "s11",
    "t3",
    "t4",
    "t5",
    "t6",
]


@app.command()
def main(
    host: str = "localhost",
    port: int = 5000,
    imitate_sail: bool = False,
    log_output: Path = Path("debug.log"),
    json_output: Path = Path("debug.json"),
    verbose: Annotated[bool, Option("-v", "--verbose")] = False,
):
    setup_logging(verbose)

    def format_status(status: StatusResponse) -> str:
        match status:
            case StatusResponse(running=False):
                state = "reset"
            case StatusResponse(paused=True):
                state = "paused"
            case _:
                state = "running"

        match status.privilege_mode:
            case 0b00:
                privilege_mode = "user"
            case 0b01:
                privilege_mode = "supervisor"
            case 0b10:
                privilege_mode = "reserved"
            case 0b11:
                privilege_mode = "machine"
            case privilege_mode:
                pass

        lines = [
            *(
                f"x{i}{'' if imitate_sail else f' ({REGISTER_NAMES[i]})'} <- 0x{value:08X}"
                for i, value in enumerate(status.registers)
            ),
            f"CSR mscratch <- 0x{status.mscratch:08X}",
            f"CSR mtvec <- 0x{status.mtvec:08X}",
            f"CSR mepc <- 0x{status.mepc:08X}",
            f"CSR mcause <- 0x{status.mcause:08X}",
            f"CSR mtval <- 0x{status.mtval:08X}",
            f"CSR mstatus <- {status.mstatus:#034b}",
            f"CSR mip <- {status.mip:#034b}",
            f"CSR mie <- {status.mie:#034b}",
            f"privilege_mode <- {privilege_mode}",
            f"state <- {state}",
            f"error_output: {status.error_output or '<empty>'}",
            "",
            f"{'[M]' if imitate_sail else 'pc'}:{f'0x{status.instruction or 0:#08X}' if imitate_sail else ''} 0x{status.pc or 0:08X}",
            *(
                []
                if imitate_sail
                else [f"instruction: {status.instruction or 0:#034b}"]
            ),
        ]

        return "\n".join(lines)

    with (
        ProcessorAccess(host, port) as processor,
        log_output.open("w", encoding="utf-8") as f,
        logging_redirect_tqdm(),
        tqdm() as bar,
    ):
        status = processor.status()
        result = [status]

        prev_formatted = format_status(status)
        f.write(prev_formatted)

        if status.running:
            processor.unpause()
        else:
            processor.start(single_step=True)

        prev_output = ""

        try:
            while True:
                processor.wait(stopped=True, paused=True)

                status = processor.status()
                result.append(status)

                bar.set_postfix_str(
                    f"pc: {status.pc:#010x}"
                    if status.pc is not None
                    else "pc: (unknown)"
                )
                bar.update(1)

                if status.error_output and status.error_output != prev_output:
                    logger.warning(status.error_output)
                prev_output = status.error_output

                # scuffed
                formatted = format_status(status)
                filtered = (
                    "\n".join(
                        line
                        for i, (line, prev_line) in enumerate(
                            zip(formatted.splitlines(), prev_formatted.splitlines())
                        )
                        if len(formatted.splitlines()) - i <= 3
                        or line != prev_line
                        or line == ""
                    )
                    + "\n"
                )
                f.write(filtered)
                prev_formatted = formatted

                if not status.running:
                    break

                processor.unpause()
        finally:
            json_output.write_bytes(TypeAdapter(list[StatusResponse]).dump_json(result))


def setup_logging(verbose: bool = False):
    if verbose:
        level = logging.DEBUG
        fmt = "[ {asctime} | {name} | {levelname} ]  {message}"
    else:
        level = logging.INFO
        fmt = "[ {asctime} | {levelname} ]  {message}"

    logging.basicConfig(
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S",
        format=fmt,
        level=level,
    )

    logger.debug("Logger initialized.")


if __name__ == "__main__":
    app()
