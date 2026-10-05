from pathlib import Path

p = Path('launcher_gui.py')
s = p.read_text(encoding='utf-8')
old = "time.sleep(.75);pt=scaled(portal,ImageGrab.grab().size);emit(f'[RUN] ANYA PORTAL -> {pt}');pyautogui.moveTo(*pt,duration=.2);pyautogui.click();deadline=time.time()+10"
new = """time.sleep(.75)
        # Botty-inspired portal interaction: visually locate A5 red portal first.
        from bot.portal_finder import find_template_center
        portal_template=APP_DIR/'assets'/'a5_red_portal.png'
        shot=ImageGrab.grab();match=find_template_center(shot,portal_template,threshold=.55)
        if match:
            pt=(match[0],match[1]);emit(f'[PORTAL] Visual match {match[2]:.3f} -> {pt}')
        else:
            pt=scaled(portal,shot.size);emit(f'[PORTAL] Visual match failed; fallback -> {pt}')
        pyautogui.moveTo(*pt,duration=.2);pyautogui.click();deadline=time.time()+10"""
if old not in s:
    raise SystemExit('Expected v23.4 portal block not found; refusing unsafe patch')
s=s.replace(old,new,1)
s=s.replace("'version':'23.4'", "'version':'23.5'", 1)
s=s.replace("SoulRunner v23.4 — GitHub Update", "SoulRunner v23.5 — Visual Portal", 1)
p.write_text(s,encoding='utf-8')
print('Applied SoulRunner v23.5 visual portal patch')
