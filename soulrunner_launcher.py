import os
import sys
import time
import queue
import threading
import subprocess
import tkinter as tk
from tkinter import messagebox

APP_NAME = "SOULRUNNER"
VERSION = "0.2-diagnostic"

class SoulRunner(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME}  {VERSION}")
        self.geometry("780x560")
        self.minsize(700, 500)
        self.configure(bg="#090806")
        self.proc = None
        self.logq = queue.Queue()
        self.started_at = None
        self.status = tk.StringVar(value="READY")
        self.step = tk.StringVar(value="Waiting for Diablo II: Resurrected")
        self.elapsed = tk.StringVar(value="00:00:00")
        self._build()
        self.bind_all("<F10>", lambda e: self.start_pause())
        self.bind_all("<F11>", lambda e: self.stop_bot())
        self.after(100, self._pump)
        self.after(1000, self._clock)

    def _build(self):
        top = tk.Frame(self, bg="#090806")
        top.pack(fill="x", padx=24, pady=(20, 8))
        tk.Label(top, text="SOULRUNNER", fg="#c8a45a", bg="#090806", font=("Georgia", 30, "bold")).pack()
        tk.Label(top, text="SANCTUARY AUTOMATION", fg="#6f6048", bg="#090806", font=("Segoe UI", 9, "bold")).pack(pady=(0, 8))
        tk.Frame(self, height=2, bg="#5b1815").pack(fill="x", padx=28)
        panel = tk.Frame(self, bg="#15110d", highlightbackground="#4b3825", highlightthickness=1)
        panel.pack(fill="x", padx=28, pady=18)
        tk.Label(panel, textvariable=self.status, fg="#d8b56a", bg="#15110d", font=("Segoe UI", 18, "bold")).pack(pady=(15, 3))
        tk.Label(panel, textvariable=self.step, fg="#b8aa91", bg="#15110d", font=("Segoe UI", 10)).pack(pady=(0, 4))
        tk.Label(panel, textvariable=self.elapsed, fg="#776b5a", bg="#15110d", font=("Consolas", 10)).pack(pady=(0, 14))
        buttons = tk.Frame(self, bg="#090806")
        buttons.pack(fill="x", padx=28)
        tk.Button(buttons, text="START  [F10]", command=self.start_pause, bg="#42110f", fg="#e0c178", activebackground="#681c17", activeforeground="#f2d58a", relief="flat", bd=0, font=("Segoe UI", 12, "bold"), padx=30, pady=12).pack(side="left", expand=True, fill="x", padx=(0, 7))
        tk.Button(buttons, text="STOP  [F11]", command=self.stop_bot, bg="#201b16", fg="#b8aa91", activebackground="#342a21", activeforeground="#e0c178", relief="flat", bd=0, font=("Segoe UI", 12, "bold"), padx=30, pady=12).pack(side="left", expand=True, fill="x", padx=(7, 0))
        logpanel = tk.Frame(self, bg="#0d0b09", highlightbackground="#34291e", highlightthickness=1)
        logpanel.pack(fill="both", expand=True, padx=28, pady=18)
        tk.Label(logpanel, text="RUN LOG", fg="#806d50", bg="#0d0b09", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=12, pady=(9, 4))
        self.log = tk.Text(logpanel, bg="#080706", fg="#aa9a80", insertbackground="#aa9a80", relief="flat", font=("Consolas", 9), height=12, state="disabled")
        self.log.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._write("SoulRunner diagnostic build ready. Start D2R, then press F10.")

    def _bot_exe(self):
        candidates = [
            os.path.join(os.path.dirname(sys.executable), "engine", "main.exe"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine", "main.exe"),
        ]
        return next((p for p in candidates if os.path.exists(p)), None)

    def _read_engine(self, pipe):
        try:
            for line in iter(pipe.readline, ''):
                line = line.rstrip()
                if line:
                    self._write("ENGINE: " + line)
        except Exception as e:
            self._write(f"LOG CAPTURE ERROR: {e}")
        finally:
            try: pipe.close()
            except Exception: pass

    def start_pause(self):
        if self.proc and self.proc.poll() is None:
            self._write("Engine already running. F11 stops it.")
            return
        exe = self._bot_exe()
        if not exe:
            messagebox.showerror(APP_NAME, "SoulRunner engine is missing. Re-extract the full ZIP.")
            return
        self.status.set("RUNNING")
        self.step.set("Nova Sorc - Pindle startup")
        self.started_at = time.time()
        self._write(f"F10: launching {exe}")
        try:
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            self.proc = subprocess.Popen([exe], cwd=os.path.dirname(exe), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, text=True, errors="replace", bufsize=1, creationflags=creationflags)
            threading.Thread(target=self._read_engine, args=(self.proc.stdout,), daemon=True).start()
            self._write("Engine launched; diagnostic output is now captured below.")
        except Exception as e:
            self.status.set("ERROR")
            self.step.set("Engine failed to start")
            self._write(f"LAUNCH ERROR: {type(e).__name__}: {e}")

    def stop_bot(self):
        if self.proc and self.proc.poll() is None:
            self._write("F11: stopping SoulRunner...")
            self.proc.terminate()
            try: self.proc.wait(timeout=3)
            except Exception: self.proc.kill()
        self.proc = None
        self.status.set("STOPPED")
        self.step.set("Press F10 to start")
        self.started_at = None

    def _write(self, msg):
        self.logq.put(f"[{time.strftime('%H:%M:%S')}] {msg}\n")

    def _pump(self):
        try:
            while True:
                msg = self.logq.get_nowait()
                self.log.configure(state="normal")
                self.log.insert("end", msg)
                self.log.see("end")
                self.log.configure(state="disabled")
        except queue.Empty:
            pass
        if self.proc and self.proc.poll() is not None:
            code = self.proc.returncode
            self.proc = None
            self.status.set("READY" if code == 0 else "ERROR")
            self.step.set(f"Engine exited with code {code}")
            self._write(f"ENGINE EXIT CODE: {code}")
            if code != 0:
                self._write("Copy the ENGINE lines above and send them to me; they contain the actual crash reason.")
        self.after(100, self._pump)

    def _clock(self):
        if self.started_at:
            s = int(time.time() - self.started_at)
            self.elapsed.set(f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}")
        else:
            self.elapsed.set("00:00:00")
        self.after(1000, self._clock)

if __name__ == "__main__":
    SoulRunner().mainloop()
