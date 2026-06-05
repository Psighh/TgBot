import tkinter as tk
from tkinter import scrolledtext
import subprocess
import threading
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

class BotDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Панель разработчика")
        self.root.geometry("800x500")
        self.root.configure(bg="#2d2d2d")

        self.process = None
        self.is_restarting = False  

        # Панель кнопок
        toolbar = tk.Frame(root, bg="#2d2d2d", pady=8)
        toolbar.pack(fill=tk.X, padx=10)

        self.btn_start = tk.Button(toolbar, text="▶ Старт", command=self.start_bot, bg="#28a745", fg="white", width=10, font=("Arial", 10, "bold"), relief=tk.FLAT)
        self.btn_start.pack(side=tk.LEFT, padx=4)

        self.btn_stop = tk.Button(toolbar, text="⏹ Стоп", command=self.stop_bot, bg="#dc3545", fg="white", width=10, font=("Arial", 10, "bold"), state=tk.DISABLED, relief=tk.FLAT)
        self.btn_stop.pack(side=tk.LEFT, padx=4)

        self.btn_restart = tk.Button(toolbar, text="🔄 Перезапуск", command=self.restart_bot, bg="#007bff", fg="white", width=12, font=("Arial", 10, "bold"), state=tk.DISABLED, relief=tk.FLAT)
        self.btn_restart.pack(side=tk.LEFT, padx=4)

        self.lbl_status = tk.Label(toolbar, text="Статус: Выключен", bg="#2d2d2d", fg="#ffc107", font=("Arial", 11, "bold"))
        self.lbl_status.pack(side=tk.RIGHT, padx=15)

        # Логи
        self.txt_logs = scrolledtext.ScrolledText(root, bg="#1e1e1e", fg="#ffffff", font=("Consolas", 10), insertbackground="white", relief=tk.FLAT)
        self.txt_logs.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def set_buttons_state(self, start="normal", stop="disabled", restart="disabled"):
        self.btn_start.config(state=start)
        self.btn_stop.config(state=stop)
        self.btn_restart.config(state=restart)

    def log(self, text):
        self.txt_logs.insert(tk.END, text)
        self.txt_logs.see(tk.END)

    def start_bot(self):
        if self.process: return
        
        self.set_buttons_state(start="disabled", stop="disabled", restart="disabled")
        self.lbl_status.config(text="Статус: Запуск...", fg="#ffc107")
        self.log("[СИСТЕМА] Запуск бота...\n")
        
        try:
            current_env = os.environ.copy()
            current_env["PYTHONIOENCODING"] = "utf-8"

            self.process = subprocess.Popen(
                [sys.executable, "-u", "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace',
                cwd=SCRIPT_DIR,
                env=current_env
            )
            
            self.set_buttons_state(start="disabled", stop="normal", restart="normal")
            self.lbl_status.config(text="Статус: Работает", fg="#28a745")

            threading.Thread(target=self.stream_logs, args=(self.process,), daemon=True).start()

        except Exception as e:
            self.log(f"[ОШИБКА ЗАПУСКА] Не удалось запустить процесс:\n{str(e)}\n")
            self.reset_ui()

    def stream_logs(self, proc):
        try:
            for line in iter(proc.stdout.readline, ''):
                self.root.after(0, self.log, line)
        except Exception as e:
            self.root.after(0, self.log, f"\n[ОШИБКА ЧТЕНИЯ ЛОГОВ]: {str(e)}\n")
        
        proc.wait()
        self.root.after(0, self.handle_process_exit, proc)

    def handle_process_exit(self, proc):
        if proc != self.process:
            return

        if self.is_restarting:
            self.is_restarting = False
            self.process = None
            self.start_bot() 
        else:
            self.reset_ui()

    def stop_bot(self):
        if not self.process: return
        self.set_buttons_state(start="disabled", stop="disabled", restart="disabled")
        self.lbl_status.config(text="Статус: Остановка...", fg="#dc3545")
        self.log("\n[СИСТЕМА] Принудительная остановка бота...\n")
        self.process.terminate()

    def restart_bot(self):
        if not self.process or self.is_restarting: return
        
        self.is_restarting = True
        self.set_buttons_state(start="disabled", stop="disabled", restart="disabled")
        self.lbl_status.config(text="Статус: Перезапуск...", fg="#007bff")
        self.log("\n[СИСТЕМА] Инициирован безопасный перезапуск...\n")
        
        self.process.terminate()

    def reset_ui(self):
        self.process = None
        self.is_restarting = False
        self.set_buttons_state(start="normal", stop="disabled", restart="disabled")
        self.lbl_status.config(text="Статус: Выключен", fg="#ffc107")

if __name__ == "__main__":
    root = tk.Tk()
    app = BotDashboard(root)
    root.mainloop()