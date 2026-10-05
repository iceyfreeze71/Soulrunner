"""SoulRunner desktop control center.

Settings-first UI: normal users should not need to edit config files.
The settings store is intentionally generic so new boss/character/inventory
options can be surfaced without redesigning the engine.
"""
import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

APP_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = APP_DIR / "soulrunner_settings.json"

DEFAULTS = {
    "character": {"profile": "Nova Sorceress", "teleport": True, "prebuff": True,
                  "energy_shield": True, "static_field": True},
    "runs": {"pindle": True, "andariel": False, "mephisto": False,
             "countess": False, "summoner": False, "travincal": False,
             "diablo": False, "baal": False, "nihlathak": False},
    "loot": {"enabled": True, "pickit": True, "stash": True, "sell_junk": True,
             "identify": True, "maintenance_interval": 5},
    "safety": {"chicken_enabled": True, "chicken_life_pct": 35,
               "merc_chicken_pct": 20, "max_failed_paths": 3},
    "game": {"difficulty": "Hell", "start_delay": 2.0, "run_delay": 0.4,
             "max_game_minutes": 8},
    "hotkeys": {"start_pause": "F10", "stop": "F11"},
    "advanced": {"debug_log": True, "template_threshold": 0.65}
}

class Settings:
    def __init__(self): self.data = self.load()
    def load(self):
        if SETTINGS_FILE.exists():
            try:
                saved=json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                out=json.loads(json.dumps(DEFAULTS))
                for section, vals in saved.items():
                    if isinstance(vals,dict) and section in out: out[section].update(vals)
                return out
            except Exception: pass
        return json.loads(json.dumps(DEFAULTS))
    def save(self): SETTINGS_FILE.write_text(json.dumps(self.data,indent=2),encoding="utf-8")

class SoulRunnerUI(tk.Tk):
    BG="#090806"; PANEL="#15110d"; GOLD="#c9a45d"; TEXT="#e7d7b8"; MUTED="#8f816c"; RED="#681713"
    def __init__(self):
        super().__init__(); self.settings=Settings(); self.title("SoulRunner — Sanctuary Control Center")
        self.geometry("1040x720"); self.minsize(900,620); self.configure(bg=self.BG)
        self.status=tk.StringVar(value="READY"); self._vars={}; self._build()
    def _build(self):
        head=tk.Frame(self,bg=self.BG); head.pack(fill="x",padx=24,pady=(18,10))
        tk.Label(head,text="SOULRUNNER",font=("Georgia",28,"bold"),fg=self.GOLD,bg=self.BG).pack(side="left")
        tk.Label(head,textvariable=self.status,font=("Segoe UI",10,"bold"),fg=self.TEXT,bg=self.PANEL,padx=18,pady=8).pack(side="right")
        body=tk.Frame(self,bg=self.BG); body.pack(fill="both",expand=True,padx=24,pady=8)
        nav=tk.Frame(body,bg=self.PANEL,width=180); nav.pack(side="left",fill="y",padx=(0,12)); nav.pack_propagate(False)
        self.content=tk.Frame(body,bg=self.BG); self.content.pack(side="left",fill="both",expand=True)
        pages=[("DASHBOARD",self.dashboard),("RUNS / BOSSES",self.runs),("CHARACTER",self.character),("LOOT / INVENTORY",self.loot),("SAFETY",self.safety),("GAME",self.game),("HOTKEYS",self.hotkeys),("ADVANCED",self.advanced)]
        for name,fn in pages: tk.Button(nav,text=name,command=fn,anchor="w",bg=self.PANEL,fg=self.TEXT,activebackground=self.RED,activeforeground="white",relief="flat",padx=15,pady=12).pack(fill="x")
        tk.Button(nav,text="SAVE ALL",command=self.save,bg=self.RED,fg="white",relief="flat",pady=12).pack(side="bottom",fill="x",padx=10,pady=10)
        self.dashboard()
    def clear(self):
        for w in self.content.winfo_children(): w.destroy()
    def titlebar(self,title,sub):
        tk.Label(self.content,text=title,font=("Georgia",22,"bold"),fg=self.GOLD,bg=self.BG).pack(anchor="w")
        tk.Label(self.content,text=sub,font=("Segoe UI",10),fg=self.MUTED,bg=self.BG).pack(anchor="w",pady=(2,16))
    def var(self,section,key):
        token=f"{section}.{key}"
        if token not in self._vars:
            val=self.settings.data[section][key]
            cls=tk.BooleanVar if isinstance(val,bool) else tk.IntVar if isinstance(val,int) else tk.DoubleVar if isinstance(val,float) else tk.StringVar
            self._vars[token]=cls(value=val)
        return self._vars[token]
    def check(self,parent,section,key,label): tk.Checkbutton(parent,text=label,variable=self.var(section,key),bg=self.PANEL,fg=self.TEXT,selectcolor=self.BG,activebackground=self.PANEL,activeforeground=self.GOLD,font=("Segoe UI",10)).pack(anchor="w",padx=16,pady=6)
    def field(self,parent,section,key,label):
        row=tk.Frame(parent,bg=self.PANEL); row.pack(fill="x",padx=16,pady=6); tk.Label(row,text=label,bg=self.PANEL,fg=self.TEXT,width=26,anchor="w").pack(side="left"); tk.Entry(row,textvariable=self.var(section,key),bg="#080706",fg=self.TEXT,insertbackground=self.TEXT,relief="flat").pack(side="left",fill="x",expand=True)
    def panel(self): p=tk.Frame(self.content,bg=self.PANEL,highlightbackground="#3c3023",highlightthickness=1); p.pack(fill="x",pady=6); return p
    def dashboard(self):
        self.clear(); self.titlebar("CONTROL CENTER","Start with Pindle, then enable more runs as their modules are added.")
        p=self.panel(); tk.Label(p,text="ENGINE",font=("Segoe UI",11,"bold"),fg=self.GOLD,bg=self.PANEL).pack(anchor="w",padx=16,pady=(14,6))
        buttons=tk.Frame(p,bg=self.PANEL); buttons.pack(fill="x",padx=16,pady=(4,16))
        tk.Button(buttons,text="START",bg=self.RED,fg="white",relief="flat",pady=12,command=lambda:self.status.set("START REQUESTED")).pack(side="left",fill="x",expand=True,padx=(0,5))
        tk.Button(buttons,text="PAUSE",bg="#282018",fg=self.TEXT,relief="flat",pady=12,command=lambda:self.status.set("PAUSED")).pack(side="left",fill="x",expand=True,padx=5)
        tk.Button(buttons,text="STOP",bg="#282018",fg=self.TEXT,relief="flat",pady=12,command=lambda:self.status.set("STOPPED")).pack(side="left",fill="x",expand=True,padx=(5,0))
        q=self.panel(); tk.Label(q,text="All normal configuration is moving into this interface. Config files remain an internal storage/debug format, not the normal setup workflow.",wraplength=720,justify="left",fg=self.TEXT,bg=self.PANEL,padx=16,pady=16).pack(anchor="w")
    def runs(self):
        self.clear(); self.titlebar("RUNS / BOSSES","Choose which runs SoulRunner should execute. Pindle is the first implementation; the UI is already multi-run.")
        p=self.panel()
        labels={"pindle":"Pindleskin","andariel":"Andariel","mephisto":"Mephisto","countess":"Countess","summoner":"Summoner","travincal":"Travincal","diablo":"Diablo","baal":"Baal","nihlathak":"Nihlathak"}
        for k,l in labels.items(): self.check(p,"runs",k,l)
    def character(self):
        self.clear(); self.titlebar("CHARACTER","Character profile and combat behavior."); p=self.panel(); self.field(p,"character","profile","Profile"); self.check(p,"character","teleport","Use Teleport"); self.check(p,"character","prebuff","Pre-buff before runs"); self.check(p,"character","energy_shield","Energy Shield"); self.check(p,"character","static_field","Static Field")
    def loot(self):
        self.clear(); self.titlebar("LOOT / INVENTORY","Control PickIt and town maintenance without editing files."); p=self.panel(); self.check(p,"loot","enabled","Loot enabled"); self.check(p,"loot","pickit","Use PickIt rules"); self.check(p,"loot","identify","Identify items"); self.check(p,"loot","stash","Stash keepers"); self.check(p,"loot","sell_junk","Sell junk"); self.field(p,"loot","maintenance_interval","Town maintenance every N runs")
    def safety(self):
        self.clear(); self.titlebar("SAFETY","Life and recovery limits."); p=self.panel(); self.check(p,"safety","chicken_enabled","Emergency exit / chicken"); self.field(p,"safety","chicken_life_pct","Chicken life %"); self.field(p,"safety","merc_chicken_pct","Merc chicken %"); self.field(p,"safety","max_failed_paths","Max failed paths")
    def game(self):
        self.clear(); self.titlebar("GAME","Run timing and game options."); p=self.panel(); self.field(p,"game","difficulty","Difficulty"); self.field(p,"game","start_delay","Start delay seconds"); self.field(p,"game","run_delay","Delay between runs"); self.field(p,"game","max_game_minutes","Max game minutes")
    def hotkeys(self):
        self.clear(); self.titlebar("HOTKEYS","Change SoulRunner controls here."); p=self.panel(); self.field(p,"hotkeys","start_pause","Start / Pause"); self.field(p,"hotkeys","stop","Stop")
    def advanced(self):
        self.clear(); self.titlebar("ADVANCED","Computer-vision and diagnostic settings."); p=self.panel(); self.check(p,"advanced","debug_log","Detailed debug logging"); self.field(p,"advanced","template_threshold","Template threshold")
    def save(self):
        for token,var in self._vars.items():
            section,key=token.split('.',1)
            try:self.settings.data[section][key]=var.get()
            except tk.TclError:return messagebox.showerror("SoulRunner",f"Invalid value for {key}")
        self.settings.save(); self.status.set("SETTINGS SAVED"); messagebox.showinfo("SoulRunner","All settings saved.")

if __name__=="__main__": SoulRunnerUI().mainloop()
