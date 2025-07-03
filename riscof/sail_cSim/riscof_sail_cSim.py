import copy
import json
import logging
import os
import re
import shutil
import subprocess
from typing import Any

import riscof.utils as utils
from riscof.pluginTemplate import pluginTemplate

logger = logging.getLogger()


class sail_cSim(pluginTemplate):
    __model__ = "sail_c_simulator"
    __version__ = "0.5.0"

    def __init__(self, *args, **kwargs):
        sclass = super().__init__(*args, **kwargs)

        config = kwargs.get("config")
        if config is None:
            logger.error("Config node for sail_cSim missing.")
            raise SystemExit(1)
        self.num_jobs = str(config["jobs"] if "jobs" in config else 1)
        self.pluginpath = os.path.abspath(config["pluginpath"])
        self.sail_exe = {
            "32": os.path.join(
                config["PATH"] if "PATH" in config else "", "sail_riscv_sim"
            ),
            "64": os.path.join(
                config["PATH"] if "PATH" in config else "", "sail_riscv_sim"
            ),
        }
        self.isa_spec = os.path.abspath(config["ispec"]) if "ispec" in config else ""
        self.platform_spec = (
            os.path.abspath(config["pspec"]) if "ispec" in config else ""
        )
        self.make = config["make"] if "make" in config else "make"
        logger.debug("SAIL CSim plugin initialised using the following configuration.")
        for entry in config:
            logger.debug(entry + " : " + config[entry])
        return sclass

    def initialise(self, suite, work_dir, archtest_env):
        self.suite = suite
        self.work_dir = work_dir
        self.objdump_cmd = "riscv{1}-unknown-elf-objdump -D {0} > {2};"
        self.compile_cmd = (
            "riscv{1}-unknown-elf-gcc -march={0} \
         -static -mcmodel=medany -fvisibility=hidden -nostdlib -nostartfiles\
         -T "
            + self.pluginpath
            + "/env/link.ld\
         -I "
            + self.pluginpath
            + "/env/\
         -I "
            + archtest_env
        )

    def build(self, isa_yaml, platform_yaml):
        ispec = utils.load_yaml(isa_yaml)["hart0"]
        self.xlen = "64" if 64 in ispec["supported_xlen"] else "32"
        self.flen = "64" if "D" in ispec["ISA"] else "32"
        self.isa_yaml_path = isa_yaml
        self.isa = "rv" + self.xlen
        self.compile_cmd = (
            self.compile_cmd
            + " -mabi="
            + ("lp64 " if 64 in ispec["supported_xlen"] else "ilp32 ")
        )
        if "I" in ispec["ISA"]:
            self.isa += "i"
        if "M" in ispec["ISA"]:
            self.isa += "m"
        if "A" in ispec["ISA"]:
            self.isa += "a"
        if "F" in ispec["ISA"]:
            self.isa += "f"
        if "D" in ispec["ISA"]:
            self.isa += "d"
        if "C" in ispec["ISA"]:
            self.isa += "c"
        objdump = "riscv{0}-unknown-elf-objdump".format(self.xlen)
        if shutil.which(objdump) is None:
            logger.error(
                objdump + ": executable not found. Please check environment setup."
            )
            raise SystemExit(1)
        compiler = "riscv{0}-unknown-elf-gcc".format(self.xlen)
        if shutil.which(compiler) is None:
            logger.error(
                compiler + ": executable not found. Please check environment setup."
            )
            raise SystemExit(1)
        if shutil.which(self.sail_exe[self.xlen]) is None:
            logger.error(
                self.sail_exe[self.xlen]
                + ": executable not found. Please check environment setup."
            )
            raise SystemExit(1)
        if shutil.which(self.make) is None:
            logger.error(
                self.make + ": executable not found. Please check environment setup."
            )
            raise SystemExit(1)

    def runTests(self, testList, cgf_file=None, header_file=None):
        sail_config_path = os.path.join(self.pluginpath, "env", "sail_config.json")

        if os.path.exists(self.work_dir + "/Makefile." + self.name[:-1]):
            os.remove(self.work_dir + "/Makefile." + self.name[:-1])
        make = utils.makeUtil(
            makefilePath=os.path.join(self.work_dir, "Makefile." + self.name[:-1])
        )
        make.makeCommand = self.make + " -j" + self.num_jobs
        for file in testList:
            testentry = testList[file]
            test = testentry["test_path"]
            test_dir = testentry["work_dir"]
            test_name = test.rsplit("/", 1)[1][:-2]

            elf = "ref.elf"

            execute = ""

            cmd = (
                self.compile_cmd.format(testentry["isa"].lower(), self.xlen)
                + " "
                + test
                + " -o "
                + elf
            )
            compile_cmd = cmd + " -D" + " -D".join(testentry["macros"])
            execute += compile_cmd + ";"

            # comment out objdump command to make the tests run faster
            execute += "#" + self.objdump_cmd.format(elf, self.xlen, "ref.dump")
            sig_file = os.path.join(test_dir, self.name[:-1] + ".signature")
            log_file = os.path.join(test_dir, test_name + ".log")

            execute += (
                self.sail_exe[self.xlen]
                + " --config={0} -v --trace=step --signature-granularity=4  --test-signature={1} {2} > {3} 2>&1;".format(
                    sail_config_path, sig_file, elf, log_file
                )
            )

            cov_str = " "
            for label in testentry["coverage_labels"]:
                cov_str += " -l " + label

            cgf_mac = " "
            header_file_flag = " "
            if header_file is not None:
                header_file_flag = f" -h {header_file} "
                cgf_mac += " -cm common "
                for macro in testentry["mac"]:
                    cgf_mac += " -cm " + macro

            if cgf_file is not None:
                coverage_cmd = "riscv_isac --verbose info coverage -d \
                        -t {0}.log --parser-name c_sail -o coverage.rpt  \
                        --sig-label begin_signature  end_signature \
                        -e ref.elf -c {1} -x{2} -f{3} {4} {5} {6};".format(
                    test_name,
                    " -c ".join(cgf_file),
                    self.xlen,
                    self.flen,
                    cov_str,
                    header_file_flag,
                    cgf_mac,
                )
            else:
                coverage_cmd = ""

            execute += coverage_cmd

            make.add_target(
                "\n\n".join(
                    "@cd "
                    + testentry["work_dir"]
                    + "; "
                    + re.sub(r" +", " ", cmd.strip())
                    for cmd in execute.split(";")
                    if cmd.strip()
                )
            )
        make.execute_all(
            self.work_dir,
            timeout=60 * 10,
        )
