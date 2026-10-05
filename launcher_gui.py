import tkinter as tk
import sys,threading,queue,time,json,ctypes
from pathlib import Path
ROOT=Path(__file__).resolve().parent
APP_DIR=Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else ROOT
CONFIG_PATH=APP_DIR/'config.json'; ROUTE_PATH=APP_DIR/'town_route.json'
events=queue.Queue(); running=False; paused=False; recording=False; record_events=[]; record_start=0.0
stop_event=threading.Event(); pause_event=threading.Event()
DEFAULT_CONFIG={'version':'23.5','reference_resolution':[1664,928],'play':[700/1664,788/928],'hell':[830/1664,480/928],'anya_portal':[0.373,0.420],'movement_wait_seconds':1.0,'update':{'release_api':'https://api.github.com/repos/iceyfreeze71/Soulrunner/releases/latest'}}
def load_config():
    if not CONFIG_PATH.exists(): CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG,indent=2),encoding='utf-8')
    try:return json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
    except:return DEFAULT_CONFIG.copy()
CFG=load_config()
def scaled(p,size):return round(p[0]*size[0]),round(p[1]*size[1])
def emit(s):events.put(('log',s))
def set_state(s):events.put(('state',s))
def checkpoint():
    while pause_event.is_set() and not stop_event.is_set():time.sleep(.08)
    return not stop_event.is_set()
def start_recording():
    global recording,record_events,record_start
    if running:emit('[RECORDER] Stop the run before recording.');return
    record_events=[];record_start=time.perf_counter();recording=True;events.put(('record_count',0));set_state('RECORDING • CLICKS: 0');emit('[RECORDER] Recording started. F9 again to save.')
def stop_recording():
    global recording
    recording=False
    if not record_events:emit('[RECORDER] No clicks recorded.');set_state('READY');return
    ROUTE_PATH.write_text(json.dumps({'version':1,'events':record_events},indent=2),encoding='utf-8');emit(f'[RECORDER] Saved {len(record_events)} clicks to town_route.json');events.put(('record_count',len(record_events)));set_state(f'READY • ROUTE: {len(record_events)} CLICKS')
def toggle_recording():stop_recording() if recording else start_recording()
def mouse_recorder_poll_loop():
    user32=ctypes.windll.user32;VK=1
    class POINT(ctypes.Structure):_fields_=[('x',ctypes.c_long),('y',ctypes.c_long)]
    was=False;last=0.0
    while True:
        try:
            down=bool(user32.GetAsyncKeyState(VK)&0x8000)
            if recording and down and not was:
                now=time.perf_counter()
                if now-last>=.08:
                    pt=POINT()
                    if user32.GetCursorPos(ctypes.byref(pt)):
                        w=max(1,user32.GetSystemMetrics(0));h=max(1,user32.GetSystemMetrics(1));globals()['record_start'],old=now,globals()['record_start'];delay=max(0,now-old);last=now
                        record_events.append({'x':pt.x/w,'y':pt.y/h,'delay':round(delay,3)});events.put(('record_count',len(record_events)));emit(f'[RECORDER] CLICK {len(record_events)} ({pt.x},{pt.y}) delay={delay:.2f}s')
            was=down;time.sleep(.008)
        except Exception as e:emit('[RECORDER ERROR] '+repr(e));time.sleep(.25)
def load_route():
    try:return json.loads(ROUTE_PATH.read_text(encoding='utf-8')).get('events',[])
    except:return []
def replay_route():
    route=load_route()
    if not route:emit('[ROUTE] No recorded route.');return False
    try:
        from PIL import ImageGrab
        import pyautogui
        size=ImageGrab.grab().size;emit(f'[ROUTE] Replaying {len(route)} clicks.')
        for i,ev in enumerate(route,1):
            if not checkpoint():return False
            end=time.time()+min(float(ev.get('delay',0)),4)
            while time.time()<end:
                if not checkpoint():return False
                time.sleep(.05)
            pt=scaled((float(ev['x']),float(ev['y'])),size);emit(f'[ROUTE] {i}/{len(route)} -> {pt}');pyautogui.moveTo(*pt,duration=.15);pyautogui.click()
        return True
    except Exception as e:emit('[ROUTE ERROR] '+repr(e));return False
def run_active_town_route():
    route=load_route()
    if not route:emit('[ROUTE] No active town_route.json.');return False
    emit(f'[ROUTE] SHARED ACTIVE ROUTE: {len(route)} clicks');return replay_route()
def test_route():
    if running or recording:return
    def work():set_state('TESTING RECORDED ROUTE');time.sleep(2);run_active_town_route();set_state('READY')
    threading.Thread(target=work,daemon=True).start()
def avg(img,b):
    px=list(img.crop(b).resize((32,32)).convert('RGB').getdata());return sum((r+g+b)/3 for r,g,b in px)/len(px)
def looks_character(im):
    w,h=im.size;return avg(im,(int(w*.35),int(h*.81),int(w*.49),int(h*.89)))>avg(im,(int(w*.70),int(h*.70),int(w*.95),int(h*.88)))+8
def looks_difficulty(im):
    w,h=im.size;return avg(im,(int(w*.43),int(h*.30),int(w*.58),int(h*.58)))>avg(im,(int(w*.68),int(h*.30),int(w*.83),int(h*.58)))+12
def bot_worker():
    global running,paused
    try:
        from PIL import ImageGrab
        import pyautogui
        from bot.perception.states import SceneDetector,Scene
        detector=SceneDetector();play=tuple(CFG['play']);hell=tuple(CFG['hell']);portal=tuple(CFG['anya_portal']);pyautogui.PAUSE=.08
        emit('[RUN] Starting in 2 seconds.');time.sleep(2)
        if not checkpoint():return
        im=ImageGrab.grab()
        if not looks_character(im):emit('[FAIL] Character-select not detected.');return
        pt=scaled(play,im.size);emit(f'[RUN] PLAY -> {pt}');pyautogui.click(*pt)
        deadline=time.time()+5
        while time.time()<deadline:
            if not checkpoint():return
            time.sleep(.2);im=ImageGrab.grab()
            if looks_difficulty(im):pt=scaled(hell,im.size);emit(f'[RUN] HELL -> {pt}');pyautogui.click(*pt);break
        else:emit('[FAIL] Difficulty not detected.');return
        emit('[RUN] Waiting for game load / Harrogath...')
        confirmed=False;deadline=time.time()+18
        while time.time()<deadline:
            if not checkpoint():return
            time.sleep(.5);scene=detector.detect(ImageGrab.grab())
            if scene==Scene.HARROGATH_RED_PORTAL:confirmed=True;emit('[RUN] Harrogath confirmed.');break
        if not confirmed:emit('[WARN] Harrogath visual confirmation missed; continuing with active town route.')
        time.sleep(.7);emit('[RUN] Starting active town route.')
        if not run_active_town_route():emit('[FAIL] Active town route unavailable.');return
        time.sleep(.75);emit('[RUN] Town route complete. Searching/clicking Anya portal target.')
        pt=scaled(portal,ImageGrab.grab().size);emit(f'[RUN] ANYA PORTAL -> {pt}');pyautogui.moveTo(*pt,duration=.2);pyautogui.click();deadline=time.time()+10
        while time.time()<deadline:
            if not checkpoint():return
            time.sleep(.4)
            if detector.detect(ImageGrab.grab())==Scene.TEMPLE:emit("[PASS] Nihlathak's Temple confirmed.");return
        emit('[FAIL] Temple not confirmed.')
    except Exception as e:emit('[ERROR] '+repr(e))
    finally:running=False;paused=False;pause_event.clear();set_state('READY')
def f10():
    global running,paused
    if recording:emit('[F10] Finish recording first.');return
    if not running:stop_event.clear();pause_event.clear();running=True;paused=False;set_state('RUNNING');threading.Thread(target=bot_worker,daemon=True).start()
    else:
        paused=not paused
        if paused:pause_event.set();set_state('PAUSED');emit('[F10] PAUSED')
        else:pause_event.clear();set_state('RUNNING');emit('[F10] RESUMED')
def f11():
    global paused
    stop_event.set();pause_event.clear();paused=False;emit('[F11] STOP requested.');set_state('STOPPING')
def hotkey_loop():
    u=ctypes.windll.user32
    for ident,vk in ((109,0x78),(110,0x79),(111,0x7A)):
        if not u.RegisterHotKey(None,ident,0x4000,vk):emit(f'[WARNING] Could not register F{ident-100}.')
    emit('[READY] F9 Record • F10 Start/Pause • F11 Stop')
    class MSG(ctypes.Structure):_fields_=[('hwnd',ctypes.c_void_p),('message',ctypes.c_uint),('wParam',ctypes.c_size_t),('lParam',ctypes.c_ssize_t),('time',ctypes.c_ulong),('x',ctypes.c_long),('y',ctypes.c_long)]
    msg=MSG()
    while u.GetMessageW(ctypes.byref(msg),None,0,0)>0:
        if msg.message==0x0312:events.put((('f9' if msg.wParam==109 else 'f10' if msg.wParam==110 else 'f11'),None))
def check_update():
    def work():
        try:
            import urllib.request,tempfile,zipfile,subprocess,shutil
            api=CFG.get('update',{}).get('release_api',DEFAULT_CONFIG['update']['release_api']);emit('[UPDATE] Checking GitHub...')
            with urllib.request.urlopen(urllib.request.Request(api,headers={'User-Agent':'SoulRunner-Updater'}),timeout=15) as r:release=json.loads(r.read().decode())
            asset=next((x for x in release.get('assets',[]) if x.get('name')=='SoulRunner-update.zip'),None)
            if not asset:emit('[UPDATE] Release package not found.');return
            tmp=Path(tempfile.gettempdir())/'SoulRunner-update.zip'
            with urllib.request.urlopen(urllib.request.Request(asset['browser_download_url'],headers={'User-Agent':'SoulRunner-Updater'}),timeout=60) as r,open(tmp,'wb') as f:shutil.copyfileobj(r,f)
            stage=APP_DIR/'update_staged';shutil.rmtree(stage,ignore_errors=True);stage.mkdir();zipfile.ZipFile(tmp).extractall(stage);emit('[UPDATE] Downloaded. Applying and restarting...');subprocess.Popen(['cmd','/c',str(APP_DIR/'APPLY_UPDATE.bat')],cwd=str(APP_DIR),creationflags=getattr(subprocess,'CREATE_NEW_CONSOLE',0));root.after(500,root.destroy)
        except Exception as e:emit('[UPDATE ERROR] '+repr(e))
    threading.Thread(target=work,daemon=True).start()
BG='#0b0908';PANEL='#17110e';GOLD='#c8a66a';RED='#6e1712';TEXT='#e4d4b5';MUTED='#9a8a72'
root=tk.Tk();root.title('SoulRunner v23.5 — GitHub Update');root.geometry('620x600');root.configure(bg=BG)
tk.Label(root,text='SOULRUNNER',font=('Georgia',28,'bold'),fg=GOLD,bg=BG).pack(pady=(22,0));tk.Label(root,text='SANCTUARY RUN CONTROLLER',font=('Georgia',9),fg=MUTED,bg=BG).pack(pady=(0,16))
state=tk.StringVar(value='READY');tk.Label(root,textvariable=state,font=('Segoe UI',13,'bold'),fg=TEXT,bg=PANEL,width=45,pady=12).pack(padx=24,fill='x');record_count_var=tk.StringVar(value='Recorder: 0 clicks');tk.Label(root,textvariable=record_count_var,font=('Consolas',10,'bold'),fg=GOLD,bg=BG).pack(pady=(7,0))
keys=tk.Frame(root,bg=BG);keys.pack(pady=15)
for col,(key,label) in enumerate((('F9','RECORD ROUTE'),('F10','START / PAUSE'),('F11','STOP'))):
    box=tk.Frame(keys,bg=PANEL,bd=1,relief='solid');box.grid(row=0,column=col,padx=6);tk.Label(box,text=key,font=('Georgia',14,'bold'),fg=GOLD,bg=PANEL,width=10).pack(pady=(8,0));tk.Label(box,text=label,font=('Segoe UI',8),fg=TEXT,bg=PANEL,width=14).pack(pady=(0,8))
tools=tk.Frame(root,bg=BG);tools.pack(pady=4);tk.Button(tools,text='RECORD TOWN ROUTE',width=22,height=2,command=toggle_recording,bg=RED,fg='white').grid(row=0,column=0,padx=6,pady=5);tk.Button(tools,text='TEST RECORDED ROUTE',width=22,height=2,command=test_route,bg=PANEL,fg=TEXT).grid(row=0,column=1,padx=6,pady=5);tk.Button(tools,text='CLEAR ROUTE',width=22,command=lambda:(ROUTE_PATH.unlink(missing_ok=True),emit('[ROUTE] Cleared.')),bg=PANEL,fg=TEXT).grid(row=1,column=0,padx=6,pady=5);tk.Button(tools,text='CHECK FOR UPDATE',width=22,command=check_update,bg=PANEL,fg=TEXT).grid(row=1,column=1,padx=6,pady=5)
tk.Label(root,text='STATUS / DEBUG',font=('Georgia',9,'bold'),fg=GOLD,bg=BG).pack(pady=(15,4));log=tk.Text(root,height=12,wrap='word',bg='#080706',fg=TEXT,insertbackground=TEXT,relief='flat',font=('Consolas',9));log.pack(fill='both',expand=True,padx=24,pady=(0,20))
def append(s):log.insert(tk.END,s+'\n');log.see(tk.END)
def pump():
    try:
        while True:
            k,v=events.get_nowait()
            if k=='log':append(v)
            elif k=='state':state.set(v)
            elif k=='record_count':record_count_var.set(f'Recorder: {v} clicks')
            elif k=='f9':toggle_recording()
            elif k=='f10':f10()
            elif k=='f11':f11()
    except queue.Empty:pass
    root.after(40,pump)
route=load_route()
if route:state.set(f'READY • SHARED ROUTE: {len(route)} CLICKS');append(f'[ROUTE] TEST and F10 share town_route.json ({len(route)} clicks).')
threading.Thread(target=hotkey_loop,daemon=True).start();threading.Thread(target=mouse_recorder_poll_loop,daemon=True).start();root.after(40,pump);root.mainloop()
