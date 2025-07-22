# Linux

## Internet access

1. Enable the mlogv32-utils socket server on port 5000.
2. Run on host:

   ```sh
   sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
   pppd file host_ppp_options
   ```

3. Run on mlogv32:

   ```sh
   pppd /dev/ttyUL1
   ping google.com
   ```

## Debugging

### objdump

```
riscv32-unknown-linux-gnu-objdump --disassembler-color=on --visualize-jumps=color --disassemble --source --line-numbers --show-all-symbols --wide output/build/vmlinux --start-address=0xc00109ac --stop-address=0xc0010a2c

riscv32-unknown-linux-gnu-objdump --disassembler-color=on --visualize-jumps=color --disassemble --source --line-numbers --show-all-symbols --wide output/build/vmlinux --disassemble=handle_irq_desc
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
