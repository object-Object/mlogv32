# compile riscv-gnu-toolchain from source

FROM debian:bookworm AS riscv-gnu-toolchain

RUN apt-get update \
    && apt-get install -y --no-install-recommends autoconf automake autotools-dev curl python3 python3-pip python3-tomli libmpc-dev libmpfr-dev libgmp-dev gawk build-essential bison flex texinfo gperf libtool patchutils bc zlib1g-dev libexpat-dev ninja-build git cmake libglib2.0-dev libslirp-dev \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/riscv/riscv-gnu-toolchain \
    && cd riscv-gnu-toolchain \
    && ./configure --prefix=/opt/riscv --with-arch=rv32i --with-abi=ilp32 \
    && make

# main image

FROM mcr.microsoft.com/devcontainers/rust:bookworm

COPY --from=ghcr.io/astral-sh/uv:0.7.6 /uv /uvx /bin/

ENV PATH=$PATH:/opt/riscv/bin

COPY --from=riscv-gnu-toolchain /opt/riscv /opt/riscv

# avoid permission issues with cargo if cargo install runs as root
USER vscode

RUN rustup toolchain install nightly-2024-11-16

RUN rustup target add riscv32i-unknown-none-elf

RUN rustup component add --toolchain nightly-2024-11-16 clippy llvm-tools

RUN cargo install cargo-binutils
