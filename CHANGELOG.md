# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2023-02-22

### Changed

- Using zimscraperlib 2.0, creating libzim8 ZIM files
- Allowing duplicated resources at different paths
- fixed succeeded status in case an exception was raised
- Updated dependencies (beautifulsoup4, Jinja2)

## [1.0.0] - 2021-11-11

- initial version
- supports topic/document/audio/video/html5/exercise content types
- uses libzim7
- multi-threaded for node processing (IO bound)
- multi-processed for media convertion (CPU bound)
- supports scraping from any node in channel
- added S3 optimization cache support
- supports custom about page, favicon and CSS
- supports scraping from any topic node
- support basic deduplication of files upon request
