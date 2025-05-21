# compile riscv-gnu-toolchain from source

FROM debian:bookworm-slim AS build

RUN apt-get update \
    && apt-get install -y --no-install-recommends autoconf automake autotools-dev curl python3 python3-pip python3-tomli libmpc-dev libmpfr-dev libgmp-dev gawk build-essential bison flex texinfo gperf libtool patchutils bc zlib1g-dev libexpat-dev ninja-build git cmake libglib2.0-dev libslirp-dev \
    && rm -rf /var/lib/apt/lists/*

ARG ARCH
ARG ABI

# require ARCH and ABI to have values
# https://stackoverflow.com/a/42144033
RUN test -n "${ARCH}"
RUN test -n "${ABI}"

# RUN git clone https://github.com/riscv/riscv-gnu-toolchain \
#     && cd riscv-gnu-toolchain \
#     && ./configure --prefix=/opt/riscv --with-arch=${ARCH} --with-abi=${ABI} \
#     && make

RUN mkdir -p /opt/riscv/bin && touch /opt/riscv/bin/.test

# main image

FROM debian:bookworm-slim

ENV PATH=$PATH:/opt/riscv/bin

COPY --from=build /opt/riscv /opt/riscv
