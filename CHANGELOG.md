# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2023-07-25

### Added
- Add `--long-description` CLI parameter to set ZIM long description
- Add `--node-ids` CLI parameter to process only few channel nodes (_useful for debugging mostly_)

### Fixed
- Fixed issue with ZIM description too long when sourced from channel metadata
- Fixed issue with ZIM icon sizes / formats
- Fix issue with ePub rendering which was outside the iframe
- Description is now limited to expected lenght and long description is set
- Icons and illustrations are squared as expected
- Many small fixes (including some bugs) detected by ruff / pyright

### Changed

- Migrate to our new Python standard (hatch, ruff, pyright, ...)
- Using zimscraperlib 3.1.1
- Updated image to `python:3.11-bookworm`
- Retry video reencoding up to three times
- Move inline javascript to dedicated files
- Move huge inline CSS to dedicated file

## [1.0.1] - 2023-02-22

### Changed

- Using zimscraperlib 2.0, creating libzim8 ZIM files
- Allowing duplicated resources at different paths
- fixed succeeded status in case an exception was raised
- Updated dependencies (beautifulsoup4, Jinja2)

## [1.0.0] - 2021-11-11

### Added
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
