## [1.0.0] - 2026-07-13

### Added
- Forum channel monitoring
- AI-powered rating of new posts in the forum channel
- Automatic promotion of high-scoring suggestions to designated channel
- Configurable scoring threshold

## [1.1.0] - 2026-07-13

### Added
- Setting custom prompt with !prompt command
- config.json file to preserve user choices of threshold and prompt
- Reporting critical errors to the promoted suggestions discord channel

### Fixed
- Threshold not saving after restart of the app

## [1.1.1] - 2026-07-15

### Added
- Multi-File structure, where most functions are not in main.py anymore

### Fixed
- Minor optimization issues such as removing redundant code by merging it together

## [2.0.0] - 2026-07-16

### Added
- PostgreSQL database support, replacing the ugly config.json
	- From now on every server has their config stored in a unified async database. Proud of this one.
- Commands to change channels to listen and forward to
- Customized help command

### Fixed
- Minor optimization issues, including moving to a database approach allows for faster work than with a file afaik
