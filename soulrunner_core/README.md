# SoulRunner Core

This directory is the migration target for the Botty-based SoulRunner engine.

The first migrated run is `run/pindle.py`. It intentionally uses the proven visual navigation flow:

- `TownManager.go_to_act(5, ...)`
- `Pather.traverse_nodes(... A5_NIHLATHAK_PORTAL ...)`
- template selection of `A5_RED_PORTAL`
- Pindle landmark confirmation
- native-teleport fixed path to Pindle safe distance
- character-specific `kill_pindle()`
- existing pickit pipeline

The next migration unit is the dependency slice required by this run: Pather + Act 5 path data/templates + TownManager + Nova Sorceress character implementation. The old click-recorder route is not part of the new core.
