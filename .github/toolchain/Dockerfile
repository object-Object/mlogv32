# compile riscv-gnu-toolchain from source

FROM debian:bookworm-slim AS build

RUN apt-get update \
    && apt-get install -y --no-install-recommends autoconf automake autotools-dev curl python3 python3-pip python3-tomli libmpc-dev libmpfr-dev libgmp-dev gawk build-essential bison flex texinfo gperf libtool patchutils bc zlib1g-dev libexpat-dev ninja-build git cmake libglib2.0-dev libslirp-dev \
    && rm -rf /var/lib/apt/lists/*

ARG ARCH
ARG ABI
ARG MAKE_ARGS

# require ARCH and ABI to have values
# https://stackoverflow.com/a/42144033
RUN test -n "${ARCH}"
RUN test -n "${ABI}"

# this commit is the last before gcc was bumped to 15
RUN git clone https://github.com/riscv/riscv-gnu-toolchain \
    && cd riscv-gnu-toolchain \
    && git checkout 23863c2ca74e6c050f0c97e7af61f5f1776aadd1 \
    && ./configure --prefix=/opt/riscv --with-arch=${ARCH} --with-abi=${ABI} \
    && make ${MAKE_ARGS}

# main image

FROM debian:bookworm-slim

ENV PATH=$PATH:/opt/riscv/bin

COPY --from=build /opt/riscv /opt/riscv
