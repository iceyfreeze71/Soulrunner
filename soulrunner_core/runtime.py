"""Runtime orchestration for the rebuilt SoulRunner core."""
from __future__ import annotations
import os
import sys
import time
from pathlib import Path
from soulrunner_core.inventory.manager import InventoryManager
from soulrunner_core.run.registry import create_default_registry


def _app_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))


def _install_upstream_path() -> Path:
    root = _app_root()
    upstream = root / "botty_upstream"
    src = upstream / "src"
    if not src.exists():
        # Development checkout fallback: allow BOTTY_UPSTREAM to point at a clone.
        env = os.environ.get("BOTTY_UPSTREAM")
        if env:
            upstream = Path(env)
            src = upstream / "src"
    if not src.exists():
        raise RuntimeError("Botty runtime is missing from this SoulRunner build")
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    # Botty resolves assets/config relative to its repository root.
    os.chdir(upstream)
    return upstream


class SoulRunnerRuntime:
    def __init__(self, settings, emit, stop_event, pause_event):
        self.settings=settings; self.emit=emit; self.stop_event=stop_event; self.pause_event=pause_event
        self.inventory=InventoryManager(settings.get("loot",{}).get("maintenance_interval",5))
        self.registry=create_default_registry()
        self._bootstrap_upstream()

    def _bootstrap_upstream(self):
        upstream = _install_upstream_path()
        self.emit("log", f"[CORE] Botty runtime loaded from {upstream}")
        try:
            from config import Config
            from pather import Pather
            from item.pickit import PickIt
            from char.sorceress import NovaSorc
            from town import TownManager, A1, A2, A3, A4, A5
        except Exception as exc:
            raise RuntimeError(f"Could not initialize navigation core: {type(exc).__name__}: {exc}") from exc

        # Use Botty's own Nova implementation and dependency construction order.
        # This preserves the proven pathing/combat behavior rather than recreating it.
        self.pather = Pather()
        self.pickit = PickIt()
        self.char = NovaSorc(Config().nova_sorc, self.pather)
        a5 = A5(self.pather, self.char)
        a4 = A4(self.pather, self.char)
        a3 = A3(self.pather, self.char)
        a2 = A2(self.pather, self.char)
        a1 = A1(self.pather, self.char)
        self.town_manager = TownManager(a1, a2, a3, a4, a5)
        self.emit("log", "[CORE] Nova Sorc + Pather + TownManager + PickIt initialized")

    def checkpoint(self):
        while self.pause_event.is_set() and not self.stop_event.is_set(): time.sleep(.1)
        return not self.stop_event.is_set()

    def run_loop(self):
        enabled=[f"run_{k}" for k,v in self.settings["runs"].items() if v]
        # Until each additional module is migrated, fail clearly instead of pretending it works.
        installed={s.key for s in self.registry.available()}
        missing=[k for k in enabled if k not in installed]
        if missing:
            raise RuntimeError("Run module(s) not installed yet: " + ", ".join(missing))
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
                    self.inventory.maintenance_complete()
                delay=float(self.settings.get("game",{}).get("run_delay",.4))
                end=time.time()+delay
                while time.time()<end:
                    if not self.checkpoint(): return
                    time.sleep(.05)
