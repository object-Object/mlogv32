FROM mcr.microsoft.com/devcontainers/rust:bookworm

COPY --from=ghcr.io/astral-sh/uv:0.7.6 /uv /uvx /bin/

ENV PATH=$PATH:/opt/riscv/bin

COPY --from=ghcr.io/object-object/mlogv32-riscv-gnu-toolchain:rv32i-ilp32 /opt/riscv /opt/riscv

# avoid permission issues with cargo if cargo install runs as root
USER vscode

RUN rustup toolchain install nightly-2024-11-16

RUN rustup target add riscv32i-unknown-none-elf

RUN rustup component add --toolchain nightly-2024-11-16 clippy llvm-tools

RUN cargo install cargo-binutils
