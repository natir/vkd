# Stage build
FROM astral/uv:python3.13-alpine AS builder

WORKDIR /app

RUN apk update
RUN apk upgrade

RUN apk add --no-cache alpine-sdk
RUN apk add --no-cache bash
RUN apk add --no-cache git
RUN apk add --no-cache make
RUN apk add --no-cache maturin

RUN curl https://sh.rustup.rs -sSf | sh -s -- --default-toolchain stable -y

RUN uv pip install --no-cache-dir --system git+https://github.com/natir/vkd
RUN strip /usr/local/lib/python3.13/site-packages/_polars_runtime_32/_polars_runtime_32.abi3.so

FROM astral/uv:python3.13-alpine AS runner

RUN apk add --no-cache bash
RUN apk add --no-cache libgcc

COPY --from=builder /usr/local /usr/local
