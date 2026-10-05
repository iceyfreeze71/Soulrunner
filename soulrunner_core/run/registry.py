"""Run registry for the rebuilt SoulRunner engine.

Boss/run modules register here so the engine is not tied to Pindle.
Pindle is the first migrated run, not a special case in the controller.
"""

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class RunSpec:
    key: str
    label: str
    factory: Callable
    enabled_by_default: bool = False


class RunRegistry:
    def __init__(self):
        self._runs: dict[str, RunSpec] = {}

    def register(self, spec: RunSpec) -> None:
        if spec.key in self._runs:
            raise ValueError(f"Run already registered: {spec.key}")
        self._runs[spec.key] = spec

    def get(self, key: str) -> RunSpec:
        return self._runs[key]

    def available(self) -> list[RunSpec]:
        return list(self._runs.values())

    def build_enabled(self, enabled_keys: list[str], **deps):
        result = []
        for key in enabled_keys:
            spec = self.get(key)
            result.append(spec.factory(**deps))
        return result


def create_default_registry() -> RunRegistry:
    # Imports stay local so future boss modules can be added independently.
    from soulrunner_core.run.pindle import Pindle

    registry = RunRegistry()
    registry.register(RunSpec(
        key="run_pindle",
        label="Pindleskin",
        factory=lambda **d: Pindle(
            d["pather"], d["town_manager"], d["char"], d["pickit"], d.get("runs", ["run_pindle"])
        ),
        enabled_by_default=True,
    ))
    return registry
