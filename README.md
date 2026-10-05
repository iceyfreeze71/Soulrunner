# SoulRunner

SoulRunner is a focused Diablo II: Resurrected automation project currently being rebuilt around the proven Botty navigation/runtime architecture.

## Current rebuild target

The first supported configuration is intentionally narrow:

**Nova Sorceress → Hell → Act 5 → Pindle → loot → exit/recreate → repeat**

The rebuild is happening on the `botty-rebuild` branch so the current `main` build remains available as a fallback until the new core is validated.

The major change is navigation: the rebuilt SoulRunner will use visual landmark/template recognition and dynamic node traversal instead of depending on a fixed recorded mouse-click route. This allows the runner to re-anchor itself as it moves through Harrogath and the Pindle approach.

SoulRunner will retain its own streamlined interface and updater. Third-party source incorporated into the rebuilt engine remains subject to its upstream license; see `UPSTREAM_BOTTY_LICENSE.txt`.

See `REBUILD_PLAN.md` for the implementation sequence.
