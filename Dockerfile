FROM python:3.11-bookworm
LABEL org.opencontainers.image.source https://github.com/openzim/kolibri

# Install necessary packages
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      locales-all \
      unzip \
      ffmpeg \
 && rm -rf /var/lib/apt/lists/* \
 && python -m pip install --no-cache-dir -U \
      pip

# Copy code + associated artifacts
COPY src /src/src
COPY pyproject.toml *.md get_js_deps.sh MANIFEST.in LICENSE *.py /src/

# Install + cleanup
RUN pip install --no-cache-dir /src \
 && rm -rf /src

# default output directory
RUN mkdir -p /output
WORKDIR /output

CMD ["kolibri2zim", "--help"]
