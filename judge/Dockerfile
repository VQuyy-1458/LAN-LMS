FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ openjdk-17-jdk-headless python3 ca-certificates && rm -rf /var/lib/apt/lists/*
COPY sandbox_entry.py /opt/sandbox_entry.py
USER 65534:65534
WORKDIR /work
