# Stage build
FROM ghcr.io/astral-sh/uv:trixie-slim

WORKDIR /app

RUN apt update
RUN apt upgrade

RUN apt install -y bash
RUN apt install -y git
RUN apt install -y python3-maturin
RUN apt install -y cargo

RUN uv pip install --break-system-packages --system git+https://github.com/natir/vkd

RUN apt remove -y git
RUN apt remove -y python3-maturin
RUN apt remove -y cargo
