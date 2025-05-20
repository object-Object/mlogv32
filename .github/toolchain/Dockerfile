# compile riscv-gnu-toolchain from source

ARG ARCH
ARG ABI

FROM debian:bookworm-slim AS build

RUN apt-get update \
    && apt-get install -y --no-install-recommends autoconf automake autotools-dev curl python3 python3-pip python3-tomli libmpc-dev libmpfr-dev libgmp-dev gawk build-essential bison flex texinfo gperf libtool patchutils bc zlib1g-dev libexpat-dev ninja-build git cmake libglib2.0-dev libslirp-dev \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/riscv/riscv-gnu-toolchain \
    && cd riscv-gnu-toolchain \
    && ./configure --prefix=/opt/riscv --with-arch=${ARCH} --with-abi=${ABI} \
    && make

# main image

FROM debian:bookworm-slim

ENV PATH=$PATH:/opt/riscv/bin

COPY --from=build /opt/riscv /opt/riscv
