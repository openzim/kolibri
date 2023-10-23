FROM node:20-alpine as zimui

WORKDIR /src
COPY zimui /src
RUN yarn install --frozen-lockfile
RUN yarn build

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

# Copy pyproject.toml and its dependencies
COPY README.md /src/
COPY scraper/pyproject.toml scraper/get_web_deps.sh scraper/hatch_build.py /src/scraper/
COPY scraper/src/kolibri2zim/__about__.py /src/scraper/src/kolibri2zim/__about__.py

# Install Python dependencies
RUN pip install --no-cache-dir /src/scraper

# Copy code + associated artifacts
COPY scraper/src /src/scraper/src
COPY *.md LICENSE /src/

# Install + cleanup
RUN pip install --no-cache-dir /src/scraper \
 && rm -rf /src/scraper

# Copy zimui build output
COPY --from=zimui /src/dist /src/zimui

# default output directory
RUN mkdir -p /output
WORKDIR /output

ENV KOLIBRI_ZIMUI_DIST=/src/zimui

CMD ["kolibri2zim", "--help"]
