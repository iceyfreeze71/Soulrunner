import os
import sys
import time
import queue
import threading
import subprocess
import tkinter as tk
from tkinter import messagebox
from urllib.request import Request, urlopen
from urllib.error import URLError
import json
import tempfile
import zipfile
import shutil

APP_NAME = "SOULRUNNER"
VERSION = "0.3-updater"
REPO = "iceyfreeze71/Soulrunner"
LATEST_RELEASE_API = f"https://api.github.com/repos/{REPO}/releases/latest"
ASSET_NAME = "SoulRunner-Nova-Pindle.zip"

class SoulRunner(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME}  {VERSION}")
        self.geometry("780x610")
        self.minsize(700, 540)
        self.configure(bg="#090806")
        self.proc = None
        self.logq = queue.Queue()
        self.started_at = None
        self.status = tk.StringVar(value="READY")
        self.step = tk.StringVar(value="Waiting for Diablo II: Resurrected")
        self.elapsed = tk.StringVar(value="00:00:00")
        self.update_text = tk.StringVar(value="CHECK FOR UPDATES")
        self.latest_asset_url = None
        self.latest_tag = None
        self._build()
        self.bind_all("<F10>", lambda e: self.start_pause())
        self.bind_all("<F11>", lambda e: self.stop_bot())
        self.after(100, self._pump)
        self.after(1000, self._clock)
        self.after(1500, lambda: threading.Thread(target=self.check_updates, daemon=True).start())

    def _build(self):
        top = tk.Frame(self, bg="#090806"); top.pack(fill="x", padx=24, pady=(20,8))
        tk.Label(top,text="SOULRUNNER",fg="#c8a45a",bg="#090806",font=("Georgia",30,"bold")).pack()
        tk.Label(top,text="SANCTUARY AUTOMATION",fg="#6f6048",bg="#090806",font=("Segoe UI",9,"bold")).pack(pady=(0,8))
        tk.Frame(self,height=2,bg="#5b1815").pack(fill="x",padx=28)
        panel=tk.Frame(self,bg="#15110d",highlightbackground="#4b3825",highlightthickness=1); panel.pack(fill="x",padx=28,pady=18)
        tk.Label(panel,textvariable=self.status,fg="#d8b56a",bg="#15110d",font=("Segoe UI",18,"bold")).pack(pady=(15,3))
        tk.Label(panel,textvariable=self.step,fg="#b8aa91",bg="#15110d",font=("Segoe UI",10)).pack(pady=(0,4))
        tk.Label(panel,textvariable=self.elapsed,fg="#776b5a",bg="#15110d",font=("Consolas",10)).pack(pady=(0,14))
        buttons=tk.Frame(self,bg="#090806"); buttons.pack(fill="x",padx=28)
        tk.Button(buttons,text="START  [F10]",command=self.start_pause,bg="#42110f",fg="#e0c178",relief="flat",font=("Segoe UI",12,"bold"),pady=12).pack(side="left",expand=True,fill="x",padx=(0,7))
        tk.Button(buttons,text="STOP  [F11]",command=self.stop_bot,bg="#201b16",fg="#b8aa91",relief="flat",font=("Segoe UI",12,"bold"),pady=12).pack(side="left",expand=True,fill="x",padx=(7,0))
        updatebar=tk.Frame(self,bg="#090806"); updatebar.pack(fill="x",padx=28,pady=(12,0))
        self.update_btn=tk.Button(updatebar,textvariable=self.update_text,command=self.update_action,bg="#2a2117",fg="#c8a45a",relief="flat",font=("Segoe UI",10,"bold"),pady=9)
        self.update_btn.pack(fill="x")
        logpanel=tk.Frame(self,bg="#0d0b09",highlightbackground="#34291e",highlightthickness=1); logpanel.pack(fill="both",expand=True,padx=28,pady=18)
        tk.Label(logpanel,text="RUN LOG",fg="#806d50",bg="#0d0b09",font=("Segoe UI",9,"bold")).pack(anchor="w",padx=12,pady=(9,4))
        self.log=tk.Text(logpanel,bg="#080706",fg="#aa9a80",insertbackground="#aa9a80",relief="flat",font=("Consolas",9),height=12,state="disabled"); self.log.pack(fill="both",expand=True,padx=10,pady=(0,10))
        self._write(f"SoulRunner {VERSION} ready. Automatic update check enabled.")

    def _bot_exe(self):
        candidates=[os.path.join(os.path.dirname(sys.executable),"engine","main.exe"),os.path.join(os.path.dirname(os.path.abspath(__file__)),"engine","main.exe")]
        return next((p for p in candidates if os.path.exists(p)),None)

    def _read_engine(self,pipe):
        try:
            for line in iter(pipe.readline,''):
                line=line.rstrip()
                if line:self._write("ENGINE: "+line)
        except Exception as e:self._write(f"LOG CAPTURE ERROR: {e}")

    def start_pause(self):
        if self.proc and self.proc.poll() is None:self._write("Engine already running. F11 stops it."); return
        exe=self._bot_exe()
        if not exe:messagebox.showerror(APP_NAME,"SoulRunner engine is missing. Re-extract the full package."); return
        self.status.set("RUNNING"); self.step.set("Nova Sorc - Pindle startup"); self.started_at=time.time(); self._write("F10: starting SoulRunner engine...")
        try:
            self.proc=subprocess.Popen([exe],cwd=os.path.dirname(exe),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,text=True,errors="replace",bufsize=1,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            threading.Thread(target=self._read_engine,args=(self.proc.stdout,),daemon=True).start(); self._write("Engine launched.")
        except Exception as e:self.status.set("ERROR"); self._write(f"LAUNCH ERROR: {e}")

    def stop_bot(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:self.proc.wait(timeout=3)
            except Exception:self.proc.kill()
        self.proc=None; self.status.set("STOPPED"); self.step.set("Press F10 to start"); self.started_at=None

    def check_updates(self):
        self.update_text.set("CHECKING GITHUB...")
        try:
            req=Request(LATEST_RELEASE_API,headers={"User-Agent":"SoulRunner-Updater","Accept":"application/vnd.github+json"})
            data=json.loads(urlopen(req,timeout=12).read().decode("utf-8"))
            self.latest_tag=data.get("tag_name","latest")
            asset=next((a for a in data.get("assets",[]) if a.get("name")==ASSET_NAME),None)
            if not asset:
                self.latest_asset_url=None; self.update_text.set("NO UPDATE PACKAGE PUBLISHED")
                self._write("Updater: latest GitHub release has no SoulRunner update package yet."); return
            self.latest_asset_url=asset["browser_download_url"]
            self.update_text.set(f"UPDATE AVAILABLE  •  {self.latest_tag}")
            self._write(f"Updater: release {self.latest_tag} is available. Click UPDATE to install it.")
        except Exception as e:
            self.latest_asset_url=None; self.update_text.set("CHECK FOR UPDATES")
            self._write(f"Updater check failed: {e}")

    def update_action(self):
        if not self.latest_asset_url:
            threading.Thread(target=self.check_updates,daemon=True).start(); return
        if self.proc and self.proc.poll() is None:
            messagebox.showinfo(APP_NAME,"Stop SoulRunner with F11 before installing an update."); return
        threading.Thread(target=self._download_and_stage,daemon=True).start()

    def _download_and_stage(self):
        try:
            self.update_text.set("DOWNLOADING UPDATE..."); self._write("Updater: downloading release package...")
            base=os.path.dirname(sys.executable)
            tempdir=tempfile.mkdtemp(prefix="soulrunner_update_")
            zpath=os.path.join(tempdir,"update.zip")
            req=Request(self.latest_asset_url,headers={"User-Agent":"SoulRunner-Updater"})
            with urlopen(req,timeout=60) as r, open(zpath,"wb") as f: shutil.copyfileobj(r,f)
            with zipfile.ZipFile(zpath,"r") as z:
                bad=z.testzip()
                if bad:raise RuntimeError(f"Corrupt update archive: {bad}")
                stage=os.path.join(tempdir,"stage"); z.extractall(stage)
            items=os.listdir(stage)
            source=stage
            if len(items)==1 and os.path.isdir(os.path.join(stage,items[0])):source=os.path.join(stage,items[0])
            bat=os.path.join(tempdir,"install_update.cmd")
            exe_name=os.path.basename(sys.executable)
            script=f'''@echo off\ntimeout /t 2 /nobreak >nul\nxcopy "{source}\\*" "{base}\\" /E /I /Y >nul\nstart "" "{os.path.join(base,exe_name)}"\nrd /s /q "{tempdir}"\n'''
            with open(bat,"w",encoding="utf-8") as f:f.write(script)
            self._write("Updater: download verified. Restarting to install..."); self.update_text.set("INSTALLING...")
            subprocess.Popen(["cmd","/c",bat],creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0)); self.after(500,self.destroy)
        except Exception as e:
            self.update_text.set("UPDATE FAILED — RETRY"); self._write(f"Updater error: {type(e).__name__}: {e}")

    def _write(self,msg):self.logq.put(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    def _pump(self):
        try:
            while True:
                msg=self.logq.get_nowait(); self.log.configure(state="normal"); self.log.insert("end",msg); self.log.see("end"); self.log.configure(state="disabled")
        except queue.Empty:pass
        if self.proc and self.proc.poll() is not None:
            code=self.proc.returncode; self.proc=None; self.status.set("READY" if code==0 else "ERROR"); self.step.set(f"Engine exited with code {code}"); self._write(f"ENGINE EXIT CODE: {code}")
        self.after(100,self._pump)
    def _clock(self):
        if self.started_at:
            s=int(time.time()-self.started_at); self.elapsed.set(f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}")
        else:self.elapsed.set("00:00:00")
        self.after(1000,self._clock)

if __name__=="__main__":SoulRunner().mainloop()
