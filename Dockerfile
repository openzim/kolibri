FROM python:3.11-bullseye
LABEL org.opencontainers.image.source https://github.com/openzim/kolibri2zim

# Install necessary packages
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends locales-all unzip ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install -U pip hatch

#COPY requirements.txt /src/
#RUN pip3 install --no-cache-dir -r /src/requirements.txt
COPY kolibri2zim /src/kolibri2zim
COPY pyproject.toml *.md get_js_deps.sh install.sh MANIFEST.in LICENSE *.py /src/
RUN cd /src/ && hatch build -t sdist && ./install.sh

# default output directory
RUN mkdir -p /output
WORKDIR /output

CMD ["kolibri2zim", "--help"]
