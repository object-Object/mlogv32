SUITE    ?= riscv-arch-test/riscv-test-suite
ENV      ?= riscv-arch-test/riscv-test-suite/env
CONFIG   ?= config.ini
WORK_DIR ?= riscof_work
DB_DIR   ?= riscof_db

ARGS = --suite $(SUITE) --env $(ENV) --config $(CONFIG) --work-dir $(WORK_DIR)

RUN_DEPS = clean-work $(WORK_DIR)/test_list.yaml

RUN_ARGS = $(ARGS) --testfile $(WORK_DIR)/test_list.yaml --no-clean

.PHONY: run run-dut run-ref validate clean clean-work

run: $(RUN_DEPS)
	riscof run $(RUN_ARGS) --no-browser

run-dut: $(RUN_DEPS)
	riscof run $(RUN_ARGS) --no-ref-run

run-ref: $(RUN_DEPS)
	riscof run $(RUN_ARGS) --no-dut-run

validate:
	riscof validateyaml --work-dir $(WORK_DIR) --config $(CONFIG)

clean: clean-work
	rm -rf $(DB_DIR)

clean-work:
	rm -rf $(WORK_DIR)

$(WORK_DIR)/test_list.yaml: $(DB_DIR)/test_list.yaml
	mkdir -p $(WORK_DIR)
	cp -r $(DB_DIR)/* $(WORK_DIR)

$(DB_DIR)/test_list.yaml: mlogv32/mlogv32_isa.yaml mlogv32/mlogv32_platform.yaml $(CONFIG)
	rm -rf $(DB_DIR)
	riscof testlist $(ARGS)
	python filter_test_list.py --work-dir $(WORK_DIR) --config $(CONFIG)
	mv $(WORK_DIR) $(DB_DIR)
