FROM debian:bookworm-slim AS build-sail

ARG SAIL_RELEASE=https://github.com/rems-project/sail/releases/download/0.19.1-linux-binary/sail.tar.gz

# presumably not all of these are required, but the sail readme doesn't say what the dependencies are
RUN apt-get update \
    && apt-get install -y --no-install-recommends pkg-config jq autoconf automake autotools-dev curl python3 python3-pip python3-tomli libmpc-dev libmpfr-dev libgmp-dev gawk build-essential bison flex texinfo gperf libtool patchutils bc zlib1g-dev libexpat-dev ninja-build git cmake libglib2.0-dev libslirp-dev \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /usr/local \
    && curl --location "${SAIL_RELEASE}" | tar xvz --directory=/usr/local --strip-components=1 \
    && git clone https://github.com/riscv/sail-riscv.git \
    && cd sail-riscv \
    && cmake -S . -B build -DCMAKE_BUILD_TYPE=RelWithDebInfo -DDOWNLOAD_GMP=FALSE -GNinja \
    && cmake --build build \
    && mkdir -p /opt/sail-riscv \
    && mv build/c_emulator/sail_riscv_sim /opt/sail-riscv/sail_riscv_sim

FROM mcr.microsoft.com/devcontainers/rust:bookworm

COPY --from=ghcr.io/astral-sh/uv:0.7.6 /uv /uvx /bin/

ENV PATH=$PATH:/opt/riscv/bin:/opt/sail-riscv

COPY --from=ghcr.io/object-object/mlogv32-riscv-gnu-toolchain:rv32ima-ilp32 /opt/riscv /opt/riscv

COPY --from=ghcr.io/object-object/mlogv32-riscv-gnu-toolchain:rv32ima-ilp32-linux /opt/riscv /opt/riscv

COPY --from=build-sail /opt/sail-riscv /opt/sail-riscv

# https://code.visualstudio.com/remote/advancedcontainers/persist-bash-history
ARG USERNAME=vscode

RUN SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
    && mkdir /commandhistory \
    && touch /commandhistory/.bash_history \
    && chown -R $USERNAME /commandhistory \
    && echo "$SNIPPET" >> "/home/$USERNAME/.bashrc"
    && sed -i '^/__bash_prompt$/d' "/home/$USERNAME/.bashrc"
# ^ fix weird issues with shell not handling line wrapping

# buildroot dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends cpio bc

# avoid permission issues with cargo if cargo install runs as root
USER ${USERNAME}

RUN rustup toolchain install nightly-2025-06-10

# NOTE: add the following to rustflags if using riscv32imac, since we don't support compressed instructions
# "-C", "target-feature=-c",
RUN rustup target add riscv32i-unknown-none-elf
RUN rustup target add riscv32im-unknown-none-elf
RUN rustup target add riscv32imac-unknown-none-elf

RUN rustup component add --toolchain nightly-2025-06-10 clippy llvm-tools

RUN cargo install cargo-binutils
