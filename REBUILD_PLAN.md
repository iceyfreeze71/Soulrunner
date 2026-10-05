# SoulRunner Core Rebuild

SoulRunner is being rebuilt around the proven upstream Botty navigation/runtime architecture while keeping a focused SoulRunner product and interface.

## Phase 1 — Foundation

- Preserve the existing `main` branch as the current fallback.
- Perform the rewrite on `botty-rebuild`.
- Keep required upstream license attribution.
- Make Pindle the first and only enabled run while the new core is validated.
- Target Nova Sorceress as the first supported character profile.

## Phase 2 — Navigation

Primary navigation will use the upstream-style visual Pather architecture rather than SoulRunner's recorded-click town route.

Initial flow:

1. Detect character/game state.
2. Create/enter Hell game.
3. Detect Act 5 / Harrogath visual references.
4. Traverse Act 5 nodes toward the Nihlathak red portal.
5. Visually acquire and enter the red portal.
6. Traverse Pindle nodes using visual re-anchoring.
7. Report navigation state and recovery attempts in the SoulRunner run log.

The old `town_route.json` mechanism remains only as a temporary fallback during migration and is not the target navigation system.

## Phase 3 — Nova Sorceress

- Teleport movement profile.
- Nova combat profile.
- Static Field support where appropriate.
- Energy Shield / armor pre-buff support.
- Configurable skill hotkeys rather than hard-coded user bindings.

## Phase 4 — Run loop

- Pindle kill confirmation / timeout.
- Loot pickup through the existing item system.
- Return/exit game.
- Recreate game and repeat.
- Recovery for failed portal/path/game creation states.

## Phase 5 — SoulRunner product layer

- SoulRunner branding/UI.
- Start, pause, stop and live state/log display.
- One-click updater retained.
- Remove/hide unrelated run configuration from the normal UI.
- Preserve advanced configuration files for debugging.

## Rule for this rebuild

Do not rewrite proven pathing/computer-vision behavior merely to make it look custom. Adapt the proven engine, keep attribution, and put SoulRunner's customization at the configuration, character, run-selection, UI, packaging and updater layers.
