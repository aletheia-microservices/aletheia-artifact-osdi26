FROM golang:1.25.0

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    time \
    ca-certificates \
    cloc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /aletheia-eval

COPY requirements.txt .

RUN python3 -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["bash"]
