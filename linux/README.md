# Linux

## Debugging

### objdump

```
riscv32-unknown-linux-gnu-objdump --disassembler-color=on --visualize-jumps=color --start-address=0xc00109ac --stop-address=0xc0010a2c --disassemble --source --line-numbers --show-all-symbols --wide output/build/vmlinux
```

### GDB

- Start the terminal server:
  ```sh
  python -m mlogv32.scripts.terminal_server
  ```
- Connect gdb to the debug port:
  ```sh
  riscv32-unknown-linux-gnu-gdb output/build/vmlinux
  tar rem host.docker.internal:5001
  ```
