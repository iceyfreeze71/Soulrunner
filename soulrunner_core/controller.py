"""SoulRunner engine controller.

Bridges the settings-first UI to the rebuilt runtime. The controller is kept
independent of Tk so hotkeys, tests and future launchers can use the same API.
"""
from __future__ import annotations
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable


class EngineState(str, Enum):
    READY="READY"; STARTING="STARTING"; RUNNING="RUNNING"; PAUSED="PAUSED"; STOPPING="STOPPING"; STOPPED="STOPPED"; ERROR="ERROR"

@dataclass
class EngineEvent:
    kind: str
    message: str

class SoulRunnerController:
    def __init__(self, settings: dict, event_sink: Callable[[EngineEvent], None] | None=None):
        self.settings=settings; self.event_sink=event_sink or (lambda e: None)
        self.state=EngineState.READY; self._stop=threading.Event(); self._pause=threading.Event(); self._thread=None
    def emit(self,kind,msg): self.event_sink(EngineEvent(kind,msg))
    def set_state(self,state): self.state=state; self.emit("state",state.value)
    def start(self):
        if self._thread and self._thread.is_alive():
            if self.state==EngineState.PAUSED: self.resume()
            return
        self._stop.clear(); self._pause.clear(); self._thread=threading.Thread(target=self._worker,daemon=True); self._thread.start()
    def pause(self):
        if self.state==EngineState.RUNNING: self._pause.set(); self.set_state(EngineState.PAUSED); self.emit("log","[ENGINE] Paused")
    def resume(self):
        if self.state==EngineState.PAUSED: self._pause.clear(); self.set_state(EngineState.RUNNING); self.emit("log","[ENGINE] Resumed")
    def stop(self):
        self.set_state(EngineState.STOPPING); self._stop.set(); self._pause.clear(); self.emit("log","[ENGINE] Stop requested")
    def _checkpoint(self):
        while self._pause.is_set() and not self._stop.is_set(): time.sleep(.1)
        return not self._stop.is_set()
    def _worker(self):
        try:
            self.set_state(EngineState.STARTING)
            delay=float(self.settings.get("game",{}).get("start_delay",2.0)); self.emit("log",f"[ENGINE] Starting in {delay:.1f}s")
            end=time.time()+delay
            while time.time()<end:
                if not self._checkpoint(): return
                time.sleep(.1)
            enabled=[k for k,v in self.settings.get("runs",{}).items() if v]
            if not enabled: raise RuntimeError("No runs are enabled")
            self.emit("log","[ENGINE] Enabled runs: "+", ".join(enabled))
            self.set_state(EngineState.RUNNING)
            # Import only when START is pressed so the UI can still open and edit
            # settings even while a runtime dependency is being repaired.
            from soulrunner_core.runtime import SoulRunnerRuntime
            runtime=SoulRunnerRuntime(self.settings, self.emit, self._stop, self._pause)
            runtime.run_loop()
        except Exception as exc:
            self.set_state(EngineState.ERROR); self.emit("log",f"[ENGINE ERROR] {type(exc).__name__}: {exc}")
        finally:
            if self.state!=EngineState.ERROR: self.set_state(EngineState.STOPPED)
