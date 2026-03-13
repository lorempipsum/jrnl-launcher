import tkinter as tk
import subprocess
import threading
import os
import sys
import logging
from pynput import keyboard

# Setup logging
logging.basicConfig(
    filename='jrnl-lncher.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = None

def get_last_entries():
    try:
        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000) if os.name == 'nt' else 0
        result = subprocess.run(['jrnl', '-n', '3'], capture_output=True, text=True, check=True, creationflags=flags)
        out = result.stdout.strip()
        return out if out else "..."
    except Exception as e:
        logging.error(f"Error fetching entries: {e}")
        return f"Error: {e}"

def add_entry(text):
    try:
        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000) if os.name == 'nt' else 0
        subprocess.run(['jrnl'], input=text, text=True, check=True, creationflags=flags)
        return True
    except Exception as e:
        logging.error(f"Error adding entry: {e}")
        return False

class JrnlApp:
    def __init__(self):
        logging.info("Initializing UI...")
        self.root = tk.Tk()
        self.root.title("jrnl-lncher")
        
        self.width = 600
        self.height_hidden = 145
        self.height_expanded = 320
        self.is_expanded = False
        
        self.root.overrideredirect(True)
        self.root.attributes("-transparentcolor", "#010101")
        self.root.attributes("-topmost", True)
        
        self.bg_color = "#121212"
        self.input_bg = "#1e1e1e"
        self.text_color = "#888888"
        self.input_text_color = "#ffffff"
        self.accent_color = "#444444"
        self.trans_color = "#010101"
        
        self.canvas = tk.Canvas(self.root, highlightthickness=0, bg=self.trans_color)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.container = tk.Frame(self.canvas, bg=self.bg_color)
        self.container_window = self.canvas.create_window(0, 0, window=self.container, anchor="nw")
        
        # UI Elements
        self.input_frame = tk.Frame(self.container, bg=self.input_bg, padx=15, pady=15)
        self.input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=(0, 15))
        
        self.input_box = tk.Text(
            self.input_frame, height=3, bg=self.input_bg, fg=self.input_text_color, 
            font=("Segoe UI", 12), insertbackground="white", 
            borderwidth=0, highlightthickness=0, wrap=tk.WORD
        )
        self.input_box.pack(fill=tk.X)

        self.toggle_btn = tk.Label(
            self.container, text="▲", bg=self.bg_color, fg=self.accent_color,
            font=("Segoe UI", 8), cursor="hand2"
        )
        self.toggle_btn.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))
        self.toggle_btn.bind("<Button-1>", lambda e: self.toggle_history())

        # FIX: pady=(0, 5) is not supported by Text widget, use pady=5 or pack/frame padding
        self.entries_text = tk.Text(
            self.container, bg=self.bg_color, fg=self.text_color, 
            font=("Consolas", 10), borderwidth=0, highlightthickness=0, 
            wrap=tk.WORD, height=8, padx=10, pady=5
        )
        
        self.update_geometry()
        self.update_canvas()
        
        self.input_box.bind("<Return>", self.handle_enter)
        self.input_box.bind("<Shift-Return>", self.handle_shift_enter)
        self.root.bind("<Escape>", lambda e: self.hide())
        
        self.root.withdraw()
        logging.info("UI initialized and hidden.")

    def update_geometry(self):
        h = self.height_expanded if self.is_expanded else self.height_hidden
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - self.width) // 2
        y = (screen_height - h) // 3
        self.root.geometry(f"{self.width}x{h}+{x}+{y}")

    def update_canvas(self):
        h = self.height_expanded if self.is_expanded else self.height_hidden
        self.canvas.config(width=self.width, height=h)
        self.canvas.delete("bg")
        self.draw_rounded_rect(0, 0, self.width, h, 15, fill=self.bg_color, tags="bg")
        self.canvas.itemconfig(self.container_window, width=self.width, height=h)

    def draw_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1, x2, y1, x2, y1+radius, x2, y1+radius, x2, y2-radius, x2, y2-radius, x2, y2, x2-radius, y2, x2-radius, y2, x1+radius, y2, x1+radius, y2, x1, y2, x1, y2-radius, x1, y2-radius, x1, y1+radius, x1, y1+radius, x1, y1]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def toggle_history(self):
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.refresh_entries()
            self.entries_text.pack(side=tk.BOTTOM, fill=tk.X)
            self.toggle_btn.config(text="▼")
        else:
            self.entries_text.pack_forget()
            self.toggle_btn.config(text="▲")
        self.update_geometry()
        self.update_canvas()

    def refresh_entries(self):
        self.entries_text.configure(state=tk.NORMAL)
        self.entries_text.delete("1.0", tk.END)
        self.entries_text.insert(tk.END, get_last_entries())
        self.entries_text.configure(state=tk.DISABLED)
        self.entries_text.see(tk.END)

    def show(self):
        logging.info("Show triggered.")
        if self.is_expanded:
            self.toggle_history()
        self.input_box.delete("1.0", tk.END)
        self.root.deiconify()
        self.root.attributes("-topmost", True)
        self.root.focus_force()
        self.root.after(10, lambda: self.input_box.focus_set())
        
    def hide(self):
        logging.info("Hide triggered.")
        self.root.withdraw()

    def handle_enter(self, event):
        if event.state & 0x0001: 
            return None
        text = self.input_box.get("1.0", tk.END).strip()
        if text:
            self.hide()
            threading.Thread(target=add_entry, args=(text,), daemon=True).start()
        return "break"

    def handle_shift_enter(self, event):
        self.input_box.insert(tk.INSERT, "\n")
        self.input_box.see(tk.INSERT)
        return "break"

    def run(self):
        self.root.mainloop()

def on_hotkey():
    logging.info("Hotkey detected!")
    if app:
        app.root.after(0, app.show)

def start_hotkey_listener():
    try:
        logging.info("Starting hotkey listener for <cmd>+j...")
        with keyboard.GlobalHotKeys({'<cmd>+j': on_hotkey}) as h:
            h.join()
    except Exception as e:
        logging.error(f"Hotkey listener error: {e}")

if __name__ == "__main__":
    try:
        app = JrnlApp()
        listener_thread = threading.Thread(target=start_hotkey_listener, daemon=True)
        listener_thread.start()
        logging.info("Service started successfully.")
        app.run()
    except Exception as e:
        logging.critical(f"Critical service error: {e}", exc_info=True)
