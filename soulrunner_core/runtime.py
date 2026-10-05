"""Runtime orchestration for the rebuilt SoulRunner core."""
import time
from soulrunner_core.inventory.manager import InventoryManager
from soulrunner_core.run.registry import create_default_registry

class SoulRunnerRuntime:
    def __init__(self, settings, emit, stop_event, pause_event):
        self.settings=settings; self.emit=emit; self.stop_event=stop_event; self.pause_event=pause_event
        self.inventory=InventoryManager(settings.get("loot",{}).get("maintenance_interval",5))
        self.registry=create_default_registry()
        self._bootstrap_upstream()
    def _bootstrap_upstream(self):
        """Construct shared Botty-derived services used by every run.

        Imports are explicit here so missing migration dependencies produce a
        useful UI log instead of preventing SoulRunner from launching.
        """
        try:
            from pather import Pather
            from town.town_manager import TownManager
            from item.pickit import PickIt
            from char.sorceress import LightSorc
            from config import Config
        except ImportError as exc:
            raise RuntimeError(f"Botty runtime dependency not migrated yet: {exc}") from exc
        self.pather=Pather(); self.town_manager=TownManager(); self.pickit=PickIt()
        # LightSorc is the upstream-compatible base while Nova-specific combat
        # is migrated; configuration remains selected from SoulRunner's UI.
        self.char=LightSorc(Config().light_sorc, self.pather, self.pickit)
        self.char.discover_capabilities()
    def checkpoint(self):
        while self.pause_event.is_set() and not self.stop_event.is_set(): time.sleep(.1)
        return not self.stop_event.is_set()
    def run_loop(self):
        enabled=[f"run_{k}" for k,v in self.settings["runs"].items() if v]
        runs=self.registry.build_enabled(enabled,pather=self.pather,town_manager=self.town_manager,char=self.char,pickit=self.pickit,runs=enabled)
        self.emit("log",f"[CORE] Loaded {len(runs)} run module(s)")
        start_loc=None
        while self.checkpoint():
            for run in runs:
                if not self.checkpoint(): return
                self.emit("log",f"[RUN] {run.name} approach")
                loc=run.approach(start_loc)
                if not loc:
                    self.emit("log",f"[RUN] {run.name} approach failed"); continue
                result=run.battle(bool(self.settings["character"].get("prebuff",True)))
                if not result:
                    self.emit("log",f"[RUN] {run.name} battle failed"); continue
                start_loc,picked=result
                self.inventory.note_run_complete(bool(picked))
                self.emit("log",f"[RUN] {run.name} complete; loot={bool(picked)}")
                if self.inventory.should_maintain():
                    self.emit("log","[INVENTORY] Town maintenance requested")
                    # Town maintenance implementation is migrated behind this
                    # boundary; do not let individual boss modules own it.
                    self.inventory.maintenance_complete()
                delay=float(self.settings.get("game",{}).get("run_delay",.4))
                end=time.time()+delay
                while time.time()<end:
                    if not self.checkpoint(): return
                    time.sleep(.05)
