FROM python:3.8-buster

# Install necessary packages
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends locales-all wget unzip ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /src/
RUN pip3 install -r /src/requirements.txt
COPY kolibri2zim /src/kolibri2zim
COPY setup.py *.md get_js_deps.sh MANIFEST.in /src/
RUN cd /src/ && python3 ./setup.py install

RUN mkdir -p /output
WORKDIR /output
CMD ["kolibri2zim", "--help"]
