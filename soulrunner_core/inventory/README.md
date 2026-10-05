# SoulRunner Inventory Core

Inventory management is a shared engine service, not Pindle-specific behavior.

The upstream Botty inventory stack contains separate modules for personal inventory, belt, stash, vendor, common inventory helpers and cube support. Its PickIt pipeline detects ground loot, applies pick rules, handles consumable needs and reports inventory/gold-full conditions.

SoulRunner will migrate/adapt that stack behind `InventoryManager` so every current and future run can use the same lifecycle:

1. Boss/run completes.
2. PickIt evaluates and collects wanted loot.
3. Inventory state is updated.
4. If maintenance is needed, the engine goes to town.
5. Identify/sell/stash/restock actions run through the migrated inventory/town systems.
6. The engine continues with the next enabled run.

Pindle is only the first registered run. Future boss modules register with `RunRegistry` and automatically share this inventory lifecycle.
