"""SoulRunner Sanctuary Control Center."""
import json, queue
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from soulrunner_core.controller import SoulRunnerController, EngineEvent

APP_DIR=Path(__file__).resolve().parent; SETTINGS_FILE=APP_DIR/'soulrunner_settings.json'
DEFAULTS={"character":{"profile":"Nova Sorceress","teleport":True,"prebuff":True,"energy_shield":True,"static_field":True},"runs":{"pindle":True,"andariel":False,"mephisto":False,"countess":False,"summoner":False,"travincal":False,"diablo":False,"baal":False,"nihlathak":False},"loot":{"enabled":True,"pickit":True,"stash":True,"sell_junk":True,"identify":True,"maintenance_interval":5},"safety":{"chicken_enabled":True,"chicken_life_pct":35,"merc_chicken_pct":20,"max_failed_paths":3},"game":{"difficulty":"Hell","start_delay":2.0,"run_delay":0.4,"max_game_minutes":8},"hotkeys":{"start_pause":"F10","stop":"F11"},"advanced":{"debug_log":True,"template_threshold":0.65}}
class Settings:
 def __init__(self):self.data=self.load()
 def load(self):
  out=json.loads(json.dumps(DEFAULTS))
  if SETTINGS_FILE.exists():
   try:
    for s,v in json.loads(SETTINGS_FILE.read_text(encoding='utf-8')).items():
     if isinstance(v,dict) and s in out:out[s].update(v)
   except Exception:pass
  return out
 def save(self):SETTINGS_FILE.write_text(json.dumps(self.data,indent=2),encoding='utf-8')
class SoulRunnerUI(tk.Tk):
 BG='#090806';PANEL='#15110d';GOLD='#c9a45d';TEXT='#e7d7b8';MUTED='#8f816c';RED='#681713'
 def __init__(self):
  super().__init__();self.settings=Settings();self.title('SoulRunner — Sanctuary Control Center');self.geometry('1040x760');self.minsize(900,650);self.configure(bg=self.BG);self.status=tk.StringVar(value='READY');self._vars={};self.events=queue.Queue();self.controller=None;self._build();self.after(50,self._pump)
 def _build(self):
  h=tk.Frame(self,bg=self.BG);h.pack(fill='x',padx=24,pady=(18,10));tk.Label(h,text='SOULRUNNER',font=('Georgia',28,'bold'),fg=self.GOLD,bg=self.BG).pack(side='left');tk.Label(h,textvariable=self.status,font=('Segoe UI',10,'bold'),fg=self.TEXT,bg=self.PANEL,padx=18,pady=8).pack(side='right')
  b=tk.Frame(self,bg=self.BG);b.pack(fill='both',expand=True,padx=24,pady=8);n=tk.Frame(b,bg=self.PANEL,width=180);n.pack(side='left',fill='y',padx=(0,12));n.pack_propagate(False);self.content=tk.Frame(b,bg=self.BG);self.content.pack(side='left',fill='both',expand=True)
  for name,fn in [('DASHBOARD',self.dashboard),('RUNS / BOSSES',self.runs),('CHARACTER',self.character),('LOOT / INVENTORY',self.loot),('SAFETY',self.safety),('GAME',self.game),('HOTKEYS',self.hotkeys),('ADVANCED',self.advanced)]:tk.Button(n,text=name,command=fn,anchor='w',bg=self.PANEL,fg=self.TEXT,activebackground=self.RED,activeforeground='white',relief='flat',padx=15,pady=12).pack(fill='x')
  tk.Button(n,text='SAVE ALL',command=lambda:self.save(False),bg=self.RED,fg='white',relief='flat',pady=12).pack(side='bottom',fill='x',padx=10,pady=10);self.dashboard()
 def clear(self):
  for w in self.content.winfo_children():w.destroy()
 def titlebar(self,t,s):tk.Label(self.content,text=t,font=('Georgia',22,'bold'),fg=self.GOLD,bg=self.BG).pack(anchor='w');tk.Label(self.content,text=s,font=('Segoe UI',10),fg=self.MUTED,bg=self.BG).pack(anchor='w',pady=(2,16))
 def var(self,s,k):
  token=f'{s}.{k}'
  if token not in self._vars:
   v=self.settings.data[s][k];cls=tk.BooleanVar if isinstance(v,bool) else tk.IntVar if isinstance(v,int) else tk.DoubleVar if isinstance(v,float) else tk.StringVar;self._vars[token]=cls(value=v)
  return self._vars[token]
 def check(self,p,s,k,l):tk.Checkbutton(p,text=l,variable=self.var(s,k),bg=self.PANEL,fg=self.TEXT,selectcolor=self.BG,activebackground=self.PANEL,activeforeground=self.GOLD,font=('Segoe UI',10)).pack(anchor='w',padx=16,pady=6)
 def field(self,p,s,k,l):
  r=tk.Frame(p,bg=self.PANEL);r.pack(fill='x',padx=16,pady=6);tk.Label(r,text=l,bg=self.PANEL,fg=self.TEXT,width=26,anchor='w').pack(side='left');tk.Entry(r,textvariable=self.var(s,k),bg='#080706',fg=self.TEXT,insertbackground=self.TEXT,relief='flat').pack(side='left',fill='x',expand=True)
 def panel(self):p=tk.Frame(self.content,bg=self.PANEL,highlightbackground='#3c3023',highlightthickness=1);p.pack(fill='x',pady=6);return p
 def dashboard(self):
  self.clear();self.titlebar('CONTROL CENTER','SoulRunner engine controls and live run output.');p=self.panel();tk.Label(p,text='ENGINE',font=('Segoe UI',11,'bold'),fg=self.GOLD,bg=self.PANEL).pack(anchor='w',padx=16,pady=(14,6));r=tk.Frame(p,bg=self.PANEL);r.pack(fill='x',padx=16,pady=(4,12));tk.Button(r,text='START',command=self.start,bg=self.RED,fg='white',relief='flat',pady=12).pack(side='left',fill='x',expand=True,padx=(0,5));tk.Button(r,text='PAUSE / RESUME',command=self.pause,bg='#282018',fg=self.TEXT,relief='flat',pady=12).pack(side='left',fill='x',expand=True,padx=5);tk.Button(r,text='STOP',command=self.stop,bg='#282018',fg=self.TEXT,relief='flat',pady=12).pack(side='left',fill='x',expand=True,padx=(5,0));self.log=tk.Text(self.content,height=18,bg='#080706',fg=self.TEXT,insertbackground=self.TEXT,relief='flat',font=('Consolas',9));self.log.pack(fill='both',expand=True,pady=8);self._log('[UI] Ready. Settings are controlled from SoulRunner.')
 def runs(self):
  self.clear();self.titlebar('RUNS / BOSSES','Enable any installed run module.');p=self.panel();labels={'pindle':'Pindleskin','andariel':'Andariel','mephisto':'Mephisto','countess':'Countess','summoner':'Summoner','travincal':'Travincal','diablo':'Diablo','baal':'Baal','nihlathak':'Nihlathak'}
  for k,l in labels.items():self.check(p,'runs',k,l)
 def character(self):self.clear();self.titlebar('CHARACTER','Character and combat behavior.');p=self.panel();self.field(p,'character','profile','Profile');self.check(p,'character','teleport','Use Teleport');self.check(p,'character','prebuff','Pre-buff');self.check(p,'character','energy_shield','Energy Shield');self.check(p,'character','static_field','Static Field')
 def loot(self):self.clear();self.titlebar('LOOT / INVENTORY','PickIt and town maintenance.');p=self.panel();self.check(p,'loot','enabled','Loot enabled');self.check(p,'loot','pickit','Use PickIt');self.check(p,'loot','identify','Identify items');self.check(p,'loot','stash','Stash keepers');self.check(p,'loot','sell_junk','Sell junk');self.field(p,'loot','maintenance_interval','Maintenance every N runs')
 def safety(self):self.clear();self.titlebar('SAFETY','Survival and recovery.');p=self.panel();self.check(p,'safety','chicken_enabled','Emergency exit / chicken');self.field(p,'safety','chicken_life_pct','Chicken life %');self.field(p,'safety','merc_chicken_pct','Merc chicken %');self.field(p,'safety','max_failed_paths','Max failed paths')
 def game(self):self.clear();self.titlebar('GAME','Game and timing options.');p=self.panel();self.field(p,'game','difficulty','Difficulty');self.field(p,'game','start_delay','Start delay seconds');self.field(p,'game','run_delay','Run delay seconds');self.field(p,'game','max_game_minutes','Max game minutes')
 def hotkeys(self):self.clear();self.titlebar('HOTKEYS','User-configurable controls.');p=self.panel();self.field(p,'hotkeys','start_pause','Start / Pause');self.field(p,'hotkeys','stop','Stop')
 def advanced(self):self.clear();self.titlebar('ADVANCED','Vision and diagnostics.');p=self.panel();self.check(p,'advanced','debug_log','Detailed debug log');self.field(p,'advanced','template_threshold','Template threshold')
 def save(self,popup=True):
  for token,var in self._vars.items():
   s,k=token.split('.',1)
   try:self.settings.data[s][k]=var.get()
   except tk.TclError:return messagebox.showerror('SoulRunner',f'Invalid value for {k}')
  self.settings.save();self.status.set('SETTINGS SAVED')
  if popup:messagebox.showinfo('SoulRunner','All settings saved.')
 def _event(self,e:EngineEvent):self.events.put(e)
 def start(self):
  self.save(False)
  if not self.controller or self.controller.state.value in ('STOPPED','ERROR','READY'):
   self.controller=SoulRunnerController(json.loads(json.dumps(self.settings.data)),self._event)
  self.controller.start()
 def pause(self):
  if not self.controller:return
  self.controller.resume() if self.controller.state.value=='PAUSED' else self.controller.pause()
 def stop(self):
  if self.controller:self.controller.stop()
 def _log(self,msg):
  if hasattr(self,'log') and self.log.winfo_exists():self.log.insert(tk.END,msg+'\n');self.log.see(tk.END)
 def _pump(self):
  try:
   while True:
    e=self.events.get_nowait()
    if e.kind=='state':self.status.set(e.message)
    else:self._log(e.message)
  except queue.Empty:pass
  self.after(50,self._pump)
if __name__=='__main__':SoulRunnerUI().mainloop()
