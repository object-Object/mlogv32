FROM mcr.microsoft.com/devcontainers/rust:bookworm

COPY --from=ghcr.io/astral-sh/uv:0.7.6 /uv /uvx /bin/

ENV PATH=$PATH:/opt/riscv/bin:/opt/sail-riscv

COPY --from=ghcr.io/object-object/mlogv32-riscv-gnu-toolchain:rv32ima-ilp32 /opt/riscv /opt/riscv

COPY --from=registry.gitlab.com/incoresemi/docker-images/compliance /usr/bin/riscv_sim_RV32 /opt/sail-riscv/

# https://code.visualstudio.com/remote/advancedcontainers/persist-bash-history
ARG USERNAME=vscode

RUN SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
    && mkdir /commandhistory \
    && touch /commandhistory/.bash_history \
    && chown -R $USERNAME /commandhistory \
    && echo "$SNIPPET" >> "/home/$USERNAME/.bashrc"

# avoid permission issues with cargo if cargo install runs as root
USER ${USERNAME}

RUN rustup toolchain install nightly-2024-11-16

# NOTE: add the following to rustflags if using riscv32imac, since we don't support compressed instructions
# "-C", "target-feature=-c",
RUN rustup target add riscv32i-unknown-none-elf
RUN rustup target add riscv32im-unknown-none-elf
RUN rustup target add riscv32imac-unknown-none-elf

RUN rustup component add --toolchain nightly-2024-11-16 clippy llvm-tools

RUN cargo install cargo-binutils
