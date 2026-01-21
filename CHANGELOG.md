# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows semantic versioning principles.

---

## [Unreleased]

### Added
- Reusable openHASP command templates (`OPENHASP_TEMPLATES`)
- Ability for multiple devices to share the same template
- Per-device template selection via `OPENHASP_DEVICES`
- Optional debug logging for `.env` loading

### Changed
- Refactored openHASP MQTT command generation logic
- Decoupled device identifiers from command sequences
- Reduced code duplication between openHASP devices
- Consolidated configuration into a single script

### Fixed
- Python version compatibility issues with type annotations
- Zabbix API parameter validation errors
- Excessive Zabbix API calls in trigger/host resolution logic

---

## [0.1.0] – Initial version

### Added
- Zabbix 7.x API integration using API token authentication
- Retrieval of active problems and severity evaluation
- Severity-to-color mapping (green / yellow / red)
- MQTT publishing to openHASP devices
- Support for multiple openHASP screens
- `.env`-based configuration loading
