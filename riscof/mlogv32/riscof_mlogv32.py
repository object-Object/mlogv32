import logging
import os
import re
import subprocess
from typing import Any

import colorlog
from mlogv32.processor_access import ProcessorAccess

import riscof.log
import riscof.utils as utils
from riscof.pluginTemplate import pluginTemplate

logger = logging.getLogger()


class mlogv32(pluginTemplate):
    name: str

    __model__ = "mlogv32"

    __version__ = "0.1.0"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        riscof.log.logger.format = "%(log_color)s%(levelname)8s%(reset)s | %(log_color)s%(asctime)s%(reset)s | %(log_color)s%(message)s%(reset)s"
        riscof.log.logger.stream.setFormatter(
            colorlog.ColoredFormatter(
                fmt=riscof.log.logger.format,
                datefmt="%Y-%m-%d %H:%M:%S",
                log_colors=riscof.log.logger.colors,
            )
        )

        config = kwargs.get("config")

        # If the config node for this DUT is missing or empty. Raise an error. At minimum we need
        # the paths to the ispec and pspec files
        if config is None:
            print("Please enter input file paths in configuration.")
            raise SystemExit(1)

        # Number of parallel jobs that can be spawned off by RISCOF
        # for various actions performed in later functions, specifically to run the tests in
        # parallel on the DUT executable. Can also be used in the build function if required.
        self.num_jobs = str(config["jobs"] if "jobs" in config else 1)

        # Path to the directory where this python file is located. Collect it from the config.ini
        self.pluginpath: str = os.path.abspath(config["pluginpath"])

        # Collect the paths to the  riscv-config absed ISA and platform yaml files. One can choose
        # to hardcode these here itself instead of picking it from the config.ini file.
        self.isa_spec: str = os.path.abspath(config["ispec"])
        self.platform_spec: str = os.path.abspath(config["pspec"])

        self.host_repo_path: str = config["host_repo_path"]
        self.riscof_repo_path: str = config["riscof_repo_path"]

        self.reloc_tests: list[str] = config["reloc_tests"].split(",")

        self.make = config["make"] if "make" in config else "make"

        # We capture if the user would like the run the tests on the target or
        # not. If you are interested in just compiling the tests and not running
        # them on the target, then following variable should be set to False
        if "target_run" in config and config["target_run"] == "0":
            self.target_run = False
        else:
            self.target_run = True

    def initialise(self, suite: str, workdir: str, env: str):
        # capture the working directory. Any artifacts that the DUT creates should be placed in this
        # directory. Other artifacts from the framework and the Reference plugin will also be placed
        # here itself.
        self.work_dir = workdir

        # capture the architectural test-suite directory.
        self.suite_dir = suite

        # Note the march is not hardwired here, because it will change for each
        # test. Similarly the output elf name and compile macros will be assigned later in the
        # runTests function
        self.compile_cmd = (
            "riscv{xlen}-unknown-elf-gcc -march={isa} \
 -static -mcmodel=medany -fvisibility=hidden -nostdlib -nostartfiles\
 -D 'MLOGV32_TEST_NAME=\"{test_name}\"'\
 -T "
            + self.pluginpath
            + "/env/{linker_script}\
 -I "
            + self.pluginpath
            + "/env/\
 -I "
            + env
            + " {test} -o {elf} {macros}"
        )

        self.objcopy_cmd = (
            "riscv{xlen}-unknown-elf-objcopy --output-target binary {elf} {binary}"
        )

        self.objdump_cmd = (
            "riscv{xlen}-unknown-elf-objdump --disassemble-all {elf} > {dump}"
        )

        # add more utility snippets here

    def build(self, isa_yaml: str, platform_yaml: str):
        # load the isa yaml as a dictionary in python.
        ispec = utils.load_yaml(isa_yaml)["hart0"]

        # capture the XLEN value by picking the max value in 'supported_xlen' field of isa yaml. This
        # will be useful in setting integer value in the compiler string (if not already hardcoded);
        self.xlen = "64" if 64 in ispec["supported_xlen"] else "32"

        # for mlogv32 start building the '--isa' argument. the self.isa is dutnmae specific and may not be
        # useful for all DUTs
        self.isa = "rv" + self.xlen
        if "I" in ispec["ISA"]:
            self.isa += "i"
        if "M" in ispec["ISA"]:
            self.isa += "m"
        if "F" in ispec["ISA"]:
            self.isa += "f"
        if "D" in ispec["ISA"]:
            self.isa += "d"
        if "C" in ispec["ISA"]:
            self.isa += "c"

        self.compile_cmd = (
            self.compile_cmd
            + " -mabi="
            + ("lp64 " if 64 in ispec["supported_xlen"] else "ilp32 ")
        )

    def runTests(self, testlist: dict[str, Any]):
        # build tests

        logger.info(f"Building {len(testlist)} tests.")

        make = utils.makeUtil(
            makeCommand=self.make + " -j" + self.num_jobs,
            makefilePath=os.path.join(self.work_dir, "Makefile." + self.name[:-1]),
            clean=True,
        )
        for testname in testlist:
            make.add_target(self.get_compile_command(testlist, testname))
        make.execute_all(timeout=10 * 60)

        # if target runs are not required then we simply exit at this point after running all
        # the makefile targets.
        if not self.target_run:
            raise SystemExit(0)

        # run tests

        with ProcessorAccess(
            "host.docker.internal",
            5000,
            log_level=logging.DEBUG,
        ) as processor:
            # we will iterate over each entry in the testlist. Each entry node will be refered to by the
            # variable testname.
            for i, testname in enumerate(testlist):
                # hack
                _, _, test_display_name = testname.partition(
                    "riscv-arch-test/riscv-test-suite/"
                )
                logger.info(
                    f"Running test {i + 1}/{len(testlist)}: {test_display_name}"
                )
                self.run_test(testlist, testname, processor)

    def get_compile_command(self, testlist: dict[str, Any], testname: str):
        # hack
        _, _, test_display_name = testname.partition(
            "riscv-arch-test/riscv-test-suite/"
        )

        # for each testname we get all its fields (as described by the testlist format)
        testentry = testlist[testname]

        # capture the directory where the artifacts of this test will be dumped/created. RISCOF is
        # going to look into this directory for the signature files
        test_dir = testentry["work_dir"]

        # we capture the path to the assembly file of this test
        test = testentry["test_path"]

        # name of the elf file after compilation of the test
        elf = "dut.elf"
        binary = "dut.bin"
        dump = "dut.dump"

        elf_file = os.path.join(test_dir, elf)
        binary_file = os.path.join(test_dir, binary)
        dump_file = os.path.join(test_dir, dump)

        # for each test there are specific compile macros that need to be enabled. The macros in
        # the testlist node only contain the macros/values. For the gcc toolchain we need to
        # prefix with "-D". The following does precisely that.
        compile_macros = " -D" + " -D".join(testentry["macros"])

        # use a different linker script for tests that require .text to be writable
        for reloc_test in self.reloc_tests:
            if reloc_test in testname:
                linker_script = "reloc.ld"
                break
        else:
            linker_script = "xip.ld"

        # substitute all variables in the compile command that we created in the initialize
        # function
        compile_cmd = self.compile_cmd.format(
            isa=testentry["isa"].lower(),
            xlen=self.xlen,
            test=test,
            elf=elf_file,
            macros=compile_macros,
            linker_script=linker_script,
            test_name=test_display_name,
        )

        objcopy_cmd = self.objcopy_cmd.format(
            xlen=self.xlen,
            elf=elf_file,
            binary=binary_file,
        )

        objdump_cmd = self.objdump_cmd.format(
            xlen=self.xlen,
            elf=elf_file,
            dump=dump_file,
        )

        return "\n\n".join(
            re.sub(r" +", " ", cmd.strip())
            for cmd in [
                compile_cmd,
                objcopy_cmd,
                # comment out objdump command to make the tests run faster
                "#" + objdump_cmd,
            ]
        )

    def run_test(
        self, testlist: dict[str, Any], testname: str, processor: ProcessorAccess
    ):
        # for each testname we get all its fields (as described by the testlist format)
        testentry = testlist[testname]

        # capture the directory where the artifacts of this test will be dumped/created. RISCOF is
        # going to look into this directory for the signature files
        test_dir = testentry["work_dir"]

        # name of the elf file after compilation of the test
        elf = "dut.elf"
        binary = "dut.bin"
        out = "out.bin"

        binary_file = os.path.join(test_dir, binary)
        out_file = os.path.join(test_dir, out)

        # hack
        binary_file_host = binary_file.replace(
            self.riscof_repo_path, self.host_repo_path
        )
        out_file_host = out_file.replace(self.riscof_repo_path, self.host_repo_path)

        # name of the signature file as per requirement of RISCOF. RISCOF expects the signature to
        # be named as DUT-<dut-name>.signature. The below variable creates an absolute path of
        # signature file.
        sig_file = os.path.join(test_dir, self.name[:-1] + ".signature")

        begin_signature = self.get_symbol_address(
            cwd=test_dir,
            elf=elf,
            symbol="begin_signature",
        )
        end_signature = self.get_symbol_address(
            cwd=test_dir,
            elf=elf,
            symbol="end_signature",
        )
        signature_length = end_signature - begin_signature
        logger.debug(f"{begin_signature=:#x} {end_signature=:#x} {signature_length=}")

        processor.stop()
        processor.flash(binary_file_host)
        processor.start()
        processor.wait(stopped=True, paused=False)
        processor.dump(out_file_host, begin_signature, signature_length)

        with open(out_file, "rb") as out, open(sig_file, "w") as sig:
            data = out.read()
            data += b"\0" * (len(data) % 4)

            for i in range(0, len(data), 4):
                # LE -> BE
                word = data[i : i + 4][::-1]
                sig.write(word.hex() + "\n")

        if msg := processor.status().error_output:
            # logger.error(f"Processor execution failed: {msg}")
            raise RuntimeError(f"Processor execution failed: {msg}")

        logger.debug(f"Finished test: {testname}")

    def get_symbol_address(self, elf: str, symbol: str, cwd: str):
        output = subprocess.check_output(
            [
                "riscv32-unknown-elf-nm",
                "--format",
                "bsd",
                "--radix",
                "x",
                elf,
            ],
            encoding="utf-8",
            cwd=cwd,
        )
        for line in output.splitlines():
            address, _, name = line.split(" ")
            if name == symbol:
                return int(address, base=16)
        raise ValueError(f"Symbol not found: {symbol}\n{output}")
