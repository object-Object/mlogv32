# mlogv32

RISC-V processor in Mindustry logic. Requires the bleeding edge version of Mindustry (for `printchar`).

## System calls

| Index (a7) | Description  | a0        | a1  | a2  | a3  | a4  | a5  | a6  | Return (a0) |
| ---------- | ------------ | --------- | --- | --- | --- | --- | --- | --- | ----------- |
| 0          | Halt         | Exit code |     |     |     |     |     |     |             |
| 1          | `printchar`  | Char      |     |     |     |     |     |     |             |
| 2          | `printflush` |           |     |     |     |     |     |     |             |
