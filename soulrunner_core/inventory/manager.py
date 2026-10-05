"""Shared inventory lifecycle for SoulRunner runs.

This is the integration boundary around the migrated Botty inventory stack.
The underlying implementation will use Botty's inventory/pickit modules; run
modules only report whether loot was picked up or inventory pressure occurred.
"""

from dataclasses import dataclass
from enum import Enum, auto


class MaintenanceReason(Enum):
    NONE = auto()
    ITEMS_PICKED = auto()
    INVENTORY_FULL = auto()
    GOLD_FULL = auto()
    FORCED = auto()


@dataclass
class InventoryState:
    runs_since_maintenance: int = 0
    items_picked_since_maintenance: bool = False
    maintenance_reason: MaintenanceReason = MaintenanceReason.NONE


class InventoryManager:
    """Coordinates loot/inventory maintenance between arbitrary boss runs."""

    def __init__(self, maintenance_interval: int = 5):
        self.state = InventoryState()
        self.maintenance_interval = max(1, maintenance_interval)

    def note_run_complete(self, picked_up_items: bool) -> None:
        self.state.runs_since_maintenance += 1
        if picked_up_items:
            self.state.items_picked_since_maintenance = True
            self.state.maintenance_reason = MaintenanceReason.ITEMS_PICKED

    def mark_inventory_full(self) -> None:
        self.state.maintenance_reason = MaintenanceReason.INVENTORY_FULL

    def mark_gold_full(self) -> None:
        self.state.maintenance_reason = MaintenanceReason.GOLD_FULL

    def should_maintain(self) -> bool:
        return (
            self.state.maintenance_reason in {MaintenanceReason.INVENTORY_FULL, MaintenanceReason.GOLD_FULL, MaintenanceReason.FORCED}
            or (
                self.state.items_picked_since_maintenance
                and self.state.runs_since_maintenance >= self.maintenance_interval
            )
        )

    def force_maintenance(self) -> None:
        self.state.maintenance_reason = MaintenanceReason.FORCED

    def maintenance_complete(self) -> None:
        self.state = InventoryState()
