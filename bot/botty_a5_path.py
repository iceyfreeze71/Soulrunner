"""Botty-style dynamic Act 5 pathing for SoulRunner.

This ports the *pathing method* used by johannes-do/botty for Harrogath ->
Nihlathak red portal: each movement node is located from visible town templates,
then the character moves to a point stored relative to that matched landmark.
It is intentionally not a fixed click recording.

Botty path: A5_TOWN_START -> A5_NIHLATHAK_PORTAL = [3,4,5,6,8,9]
Source/MIT attribution: THIRD_PARTY_NOTICES.md
"""
from pathlib import Path
import sys, time

# Exact Botty A5 node data needed for the portal route.
NODES = {
    3: {'a5_town_1': (-276, 94), 'a5_town_2': (485, -60), 'a5_town_11': (-500, 56)},
    4: {'a5_town_1': (-467, 267), 'a5_town_2': (293, 113), 'a5_town_3': (-267, -139), 'a5_town_4': (162, -163)},
    5: {'a5_town_2': (363, 259), 'a5_town_3': (-197, 7), 'a5_town_4': (232, -17)},
    6: {'a5_town_3': (-503, 235), 'a5_town_4': (-75, 211), 'a5_town_5': (67, -180), 'a5_town_6': (387, 121)},
    8: {'a5_town_6': (127, 293), 'a5_town_5': (-195, -5), 'a5_red_portal': (598, -87)},
    9: {'a5_town_5': (-407, 167), 'a5_red_portal': (386, 85)},
}
PATH = [3, 4, 5, 6, 8, 9]


def _asset_dir():
    root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
    return root / 'assets'


def _match(screen, names, threshold=.60):
    try:
        import cv2, numpy as np
    except Exception:
        return None
    rgb = np.array(screen.convert('RGB'))
    hay = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    # Botty targets 1280x720. Scale its templates/offsets to current D2R capture.
    scale = min(screen.size[0] / 1280.0, screen.size[1] / 720.0)
    best = None
    for name in names:
        p = _asset_dir() / (name + '.png')
        needle = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
        if needle is None:
            continue
        nw, nh = max(8, round(needle.shape[1]*scale)), max(8, round(needle.shape[0]*scale))
        if nw >= hay.shape[1] or nh >= hay.shape[0]:
            continue
        needle = cv2.resize(needle, (nw, nh), interpolation=cv2.INTER_CUBIC if scale >= 1 else cv2.INTER_AREA)
        res = cv2.matchTemplate(hay, needle, cv2.TM_CCOEFF_NORMED)
        _, score, _, loc = cv2.minMaxLoc(res)
        cand = (float(score), name, loc[0] + nw//2, loc[1] + nh//2, scale)
        if best is None or cand[0] > best[0]:
            best = cand
    return best if best and best[0] >= threshold else None


def traverse_to_anya_portal(grab, click, emit=print, checkpoint=lambda: True, threshold=.60):
    """Traverse Botty nodes [3,4,5,6,8,9]. Returns True on completion."""
    emit('[BOTTY PATH] Dynamic Harrogath path starting: nodes 3,4,5,6,8,9')
    for idx in PATH:
        deadline = time.time() + 6.0
        match = None
        while time.time() < deadline and checkpoint():
            shot = grab()
            match = _match(shot, NODES[idx].keys(), threshold)
            if match:
                break
            time.sleep(.12)
        if not checkpoint():
            return False
        if not match:
            emit(f'[BOTTY PATH] FAIL node {idx}: no landmark matched')
            return False
        score, name, cx, cy, scale = match
        dx, dy = NODES[idx][name]
        x, y = round(cx + dx*scale), round(cy + dy*scale)
        w, h = shot.size
        x, y = max(8, min(w-8, x)), max(8, min(h-8, y))
        emit(f'[BOTTY PATH] node {idx} via {name} conf={score:.3f} -> ({x},{y})')
        click(x, y)
        time.sleep(.65)
    emit('[BOTTY PATH] Reached portal approach.')
    return True
