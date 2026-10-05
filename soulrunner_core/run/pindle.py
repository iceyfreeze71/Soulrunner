"""SoulRunner Pindle run adapter.

Derived from the upstream Botty Pindle run architecture. See
UPSTREAM_BOTTY_LICENSE.txt. This module deliberately keeps navigation
visual/dynamic: town traversal uses Pather nodes and the portal itself is
selected by template rather than by a fixed screen coordinate.
"""

from char import IChar
from logger import Logger
from pather import Location, Pather
from item.pickit import PickIt
import template_finder
from town.town_manager import TownManager
from utils.misc import wait
from ui import loading


class Pindle:
    name = "run_pindle"

    def __init__(self, pather: Pather, town_manager: TownManager, char: IChar, pickit: PickIt, runs: list[str]):
        self._pather = pather
        self._town_manager = town_manager
        self._char = char
        self._pickit = pickit
        self.runs = runs

    def approach(self, start_loc: Location) -> bool | Location:
        Logger.info("SoulRunner: Pindle approach")
        loc = self._town_manager.go_to_act(5, start_loc)
        if not loc:
            Logger.error("SoulRunner: could not reach Act 5")
            return False

        Logger.info("SoulRunner: traversing visual Act 5 nodes to red portal")
        if not self._pather.traverse_nodes((loc, Location.A5_NIHLATHAK_PORTAL), self._char):
            Logger.error("SoulRunner: Act 5 node traversal failed")
            return False

        wait(0.25, 0.35)
        found_loading_screen = lambda: loading.wait_for_loading_screen(2.0)
        Logger.info("SoulRunner: acquiring A5_RED_PORTAL template")
        if not self._char.select_by_template("A5_RED_PORTAL", found_loading_screen, telekinesis=False):
            Logger.error("SoulRunner: red portal template acquisition failed")
            return False

        Logger.info("SoulRunner: entered red portal")
        return Location.A5_PINDLE_START

    def battle(self, do_pre_buff: bool) -> bool | tuple[Location, bool]:
        Logger.info("SoulRunner: confirming Pindle area")
        if not template_finder.search_and_wait(["PINDLE_0", "PINDLE_1"], threshold=0.65, timeout=12).valid:
            Logger.error("SoulRunner: Pindle landmark not found")
            return False

        if do_pre_buff:
            self._char.pre_buff()

        if self._char.capabilities.can_teleport_natively:
            Logger.info("SoulRunner: teleporting fixed Pindle safe-distance path")
            self._pather.traverse_nodes_fixed("pindle_safe_dist", self._char)
        else:
            Logger.info("SoulRunner: traversing dynamic Pindle nodes")
            if not self._pather.traverse_nodes((Location.A5_PINDLE_START, Location.A5_PINDLE_SAFE_DIST), self._char):
                return False

        Logger.info("SoulRunner: engaging Pindle")
        self._char.kill_pindle()
        wait(0.2, 0.3)
        picked_up_items = self._pickit.pick_up_items(self._char)
        return Location.A5_PINDLE_END, picked_up_items
