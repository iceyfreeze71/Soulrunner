"""Template-based portal targeting adapted for SoulRunner.

Design inspired by Botty's Pindle approach: navigate near Anya's portal first,
then identify the A5 red portal visually and click the detected target rather
than relying on one hard-coded screen coordinate.

Botty source: https://github.com/johannes-do/botty
Botty license: MIT. See THIRD_PARTY_NOTICES.md.
"""
from pathlib import Path


def find_template_center(screen, template_path, threshold=0.58):
    """Return (x, y, confidence) for the best template match, else None.

    Uses OpenCV when available. The template may be searched at several nearby
    scales so the matcher is less brittle across UI/render scaling.
    """
    try:
        import cv2
        import numpy as np
    except Exception:
        return None

    path = Path(template_path)
    if not path.exists():
        return None

    hay = cv2.cvtColor(np.array(screen.convert("RGB")), cv2.COLOR_RGB2GRAY)
    needle0 = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if needle0 is None:
        return None

    best = None
    for scale in (0.80, 0.90, 1.00, 1.10, 1.20):
        nw = max(8, int(needle0.shape[1] * scale))
        nh = max(8, int(needle0.shape[0] * scale))
        if nw >= hay.shape[1] or nh >= hay.shape[0]:
            continue
        needle = cv2.resize(needle0, (nw, nh), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
        result = cv2.matchTemplate(hay, needle, cv2.TM_CCOEFF_NORMED)
        _, score, _, loc = cv2.minMaxLoc(result)
        if best is None or score > best[2]:
            best = (loc[0] + nw // 2, loc[1] + nh // 2, float(score))

    if best and best[2] >= threshold:
        return best
    return None
