FROM python:3.12-bookworm
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

# Copy pyproject.toml and its dependencies
COPY pyproject.toml openzim.toml README.md /src/
COPY src/kolibri2zim/__about__.py /src/src/kolibri2zim/__about__.py

# Install Python dependencies
RUN pip install --no-cache-dir /src

# Copy code + associated artifacts
COPY src /src/src
COPY *.md LICENSE *.py /src/

# Install + cleanup
RUN pip install --no-cache-dir /src \
 && rm -rf /src

# default output directory
RUN mkdir -p /output
WORKDIR /output

CMD ["kolibri2zim", "--help"]
