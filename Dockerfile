FROM python:3.12-slim

# Proxy support — set at build time or runtime
# docker build --build-arg HTTP_PROXY=http://proxy:8080 ...
# docker run -e HTTP_PROXY=http://proxy:8080 ...
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ENV HTTP_PROXY=${HTTP_PROXY} \
    HTTPS_PROXY=${HTTPS_PROXY} \
    NO_PROXY=${NO_PROXY}

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Pre-install dependencies into a cached venv so runs are instant
WORKDIR /app
COPY market_overview.py .
RUN uv venv /app/.venv && \
    uv pip install --python /app/.venv/bin/python yfinance rich lxml pandas

ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"

# Default: portfolio view
ENTRYPOINT ["python", "market_overview.py"]
CMD ["-p"]
