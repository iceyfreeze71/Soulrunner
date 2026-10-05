from enum import Enum

class Scene(Enum):
    UNKNOWN='unknown'
    HARROGATH='harrogath'
    HARROGATH_RED_PORTAL='harrogath_red_portal'
    TEMPLE='nihlathaks_temple'

def _red_portal_score(im):
    w,h=im.size
    gh=min(h,int(h*.82))
    box=(int(w*.15),int(gh*.20),int(w*.42),int(gh*.66))
    px=list(im.crop(box).resize((100,100)).convert('RGB').getdata())
    return sum(1 for r,g,b in px if r>135 and r>g*1.35 and r>b*1.12)

class SceneDetector:
    def __init__(self):
        self.saw_harrogath_portal=False

    def detect(self,image):
        red=_red_portal_score(image)>500
        if red:
            self.saw_harrogath_portal=True
            return Scene.HARROGATH_RED_PORTAL
        if self.saw_harrogath_portal:
            return Scene.TEMPLE
        return Scene.UNKNOWN
