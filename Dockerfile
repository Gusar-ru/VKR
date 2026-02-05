FROM python:3.13-slim
WORKDIR /opt
COPY requirements.txt /opt/requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake ninja-build libffi-dev pkg-config \
 && rm -rf /var/lib/apt/lists/* \
 && python -m pip install --upgrade pip \
 && pip install -r /opt/requirements.txt
COPY . /opt
CMD ["python", "main.py"]
