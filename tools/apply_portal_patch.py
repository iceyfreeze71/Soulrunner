from pathlib import Path

p = Path('launcher_gui.py')
s = p.read_text(encoding='utf-8')

# Replace the shared recorded-route entry point with Botty's dynamic A5 town path.
old_route = """def run_active_town_route():
    route=load_route()
    if not route:emit('[ROUTE] No active town_route.json.');return False
    emit(f'[ROUTE] SHARED ACTIVE ROUTE: {len(route)} clicks');return replay_route()"""
new_route = """def run_active_town_route():
    # Botty dynamic path: detect Harrogath landmarks at every node instead of
    # replaying absolute recorded clicks.
    try:
        from PIL import ImageGrab
        import pyautogui
        from bot.botty_a5_path import traverse_to_anya_portal
        emit('[ROUTE] BOTTY DYNAMIC A5 PATH (recorded route bypassed).')
        return traverse_to_anya_portal(ImageGrab.grab, pyautogui.click, emit, checkpoint)
    except Exception as e:
        emit('[BOTTY PATH ERROR] '+repr(e));return False"""
if old_route not in s:
    raise SystemExit('Expected route entry point not found; refusing patch')
s=s.replace(old_route,new_route,1)

# Keep visual portal selection after Botty has dynamically reached it.
old_portal = "time.sleep(.75);pt=scaled(portal,ImageGrab.grab().size);emit(f'[RUN] ANYA PORTAL -> {pt}');pyautogui.moveTo(*pt,duration=.2);pyautogui.click();deadline=time.time()+10"
new_portal = """time.sleep(.75)
        from bot.portal_finder import find_template_center
        import sys
        asset_root=Path(getattr(sys,'_MEIPASS',APP_DIR))/'assets'
        portal_template=asset_root/'a5_red_portal.png'
        shot=ImageGrab.grab();match=find_template_center(shot,portal_template,threshold=.55)
        if match:
            pt=(match[0],match[1]);emit(f'[PORTAL] Visual match {match[2]:.3f} -> {pt}')
        else:
            emit('[PORTAL] Visual portal match failed after Botty path.');return
        pyautogui.moveTo(*pt,duration=.2);pyautogui.click();deadline=time.time()+10"""
if old_portal not in s:
    raise SystemExit('Expected portal block not found; refusing patch')
s=s.replace(old_portal,new_portal,1)

s=s.replace("'version':'23.4'", "'version':'24.0'", 1)
s=s.replace("SoulRunner v23.4 — GitHub Update", "SoulRunner v24.0 — Botty Dynamic Path", 1)
s=s.replace("TEST RECORDED ROUTE", "TEST BOTTY ROUTE")
s=s.replace("Using SAME route function as TEST RECORDED ROUTE.", "Using Botty dynamic Act 5 route.")
p.write_text(s,encoding='utf-8')
print('Applied SoulRunner v24.0 Botty dynamic Act 5 path')
