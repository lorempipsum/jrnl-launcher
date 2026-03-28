import tkinter as tk
import subprocess
import threading
import os
import sys
import logging
import shutil
import uuid
from dotenv import load_dotenv
from pynput import keyboard
from PIL import Image, ImageGrab, ImageTk
import windnd

import socket

load_dotenv()

# Prevent multiple instances using a TCP socket lock
def get_lock():
    try:
        # Create a socket and bind it to a specific port.
        # This will fail if another instance is already running and has bound the port.
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lock_socket.bind(('127.0.0.1', 56789))
        return lock_socket
    except socket.error:
        return None

_lock_socket = get_lock()
if not _lock_socket:
    # We can't log to the file yet as logging isn't setup, 
    # but we can print and exit immediately.
    print("Another instance of jrnl-launcher is already running. Exiting.")
    sys.exit(0)

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
        self.height_hidden = 130
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
        self.attachments = []
        
        self.input_frame = tk.Frame(self.container, bg=self.input_bg, padx=10, pady=8)
        self.input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=(0, 10))
        
        self.input_box = tk.Text(
            self.input_frame, height=2, bg=self.input_bg, fg=self.input_text_color, 
            font=("Segoe UI", 12), insertbackground="white", 
            borderwidth=0, highlightthickness=0, wrap=tk.WORD
        )
        self.input_box.pack(fill=tk.X)

        self.attachments_frame = tk.Frame(self.container, bg=self.bg_color)
        self.attachments_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=15)

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
        self.input_box.bind("<<Paste>>", self.handle_paste)
        self.root.bind("<Escape>", lambda e: self.hide())
        
        try:
            windnd.hook_dropfiles(self.root, self.handle_drop)
        except Exception as e:
            logging.error(f"Failed to hook windnd: {e}")
        
        self.root.withdraw()
        logging.info("UI initialized and hidden.")

    def get_jrnl_media_path(self):
        if getattr(self, "cached_media_path", None):
            return self.cached_media_path
            
        try:
            result = subprocess.run(['jrnl', '--list'], capture_output=True, text=True, check=True)
            for line in result.stdout.splitlines():
                if "default ->" in line:
                    jrnl_path = line.split("->")[1].strip()
                    media_path = os.path.join(os.path.dirname(jrnl_path), "jrnl-media")
                    if not os.path.exists(media_path):
                        os.makedirs(media_path)
                    self.cached_media_path = media_path
                    return media_path
        except Exception as e:
            logging.error(f"Error finding jrnl path: {e}")
        return None

    def handle_drop(self, files):
        for f in files:
            try:
                file_path = f.decode('gbk') if isinstance(f, bytes) else f
                if os.path.isfile(file_path):
                    self.add_attachment(file_path, is_clipboard=False)
            except Exception as e:
                logging.error(f"Error handling drop: {e}")

    def handle_paste(self, event):
        try:
            img = ImageGrab.grabclipboard()
            if img:
                self.add_attachment(img, is_clipboard=True)
                return "break"
        except Exception as e:
            logging.error(f"Error handling paste: {e}")
            
    def add_attachment(self, data, is_clipboard):
        frame = tk.Frame(self.attachments_frame, bg=self.bg_color)
        frame.pack(side=tk.TOP, fill=tk.X, pady=1)
        
        thumb_label = tk.Label(frame, bg=self.bg_color)
        thumb_label.pack(side=tk.LEFT)
        
        if is_clipboard:
            img = data.copy()
            img.thumbnail((24, 24))
            photo = ImageTk.PhotoImage(img)
            thumb_label.config(image=photo)
            thumb_label.image = photo
            original_name = "Pasted Image"
        else:
            original_name = os.path.basename(data)
            try:
                img = Image.open(data)
                img.thumbnail((24, 24))
                photo = ImageTk.PhotoImage(img)
                thumb_label.config(image=photo)
                thumb_label.image = photo
            except Exception:
                thumb_label.config(text="📄", fg=self.text_color, width=4)
                
        name_var = tk.StringVar(value=original_name)
        name_label = tk.Label(frame, textvariable=name_var, bg=self.bg_color, fg=self.text_color, font=("Segoe UI", 9))
        name_label.pack(side=tk.LEFT, padx=5)
        
        # Build markdown link reference to insert in the text box
        link_ref = f"[{original_name}]({original_name})"
        
        attachment_obj = {
            "data": data,
            "is_clipboard": is_clipboard,
            "name_var": name_var,
            "frame": frame,
            "link_ref": link_ref,
        }

        remove_btn = tk.Button(frame, text="✕", bg=self.bg_color, fg=self.text_color, borderwidth=0, cursor="hand2", font=("Segoe UI", 8), command=lambda: self.remove_attachment(attachment_obj))
        remove_btn.pack(side=tk.RIGHT)
        
        # Insert markdown link in the text box
        self.input_box.insert(tk.INSERT, link_ref + " ")
        
        self.attachments.append(attachment_obj)

    def remove_attachment(self, attachment_obj):
        if attachment_obj in self.attachments:
            self.attachments.remove(attachment_obj)
        attachment_obj["frame"].destroy()
        # Remove the markdown link reference from the text box
        link_ref = attachment_obj.get("link_ref", "")
        if link_ref:
            content = self.input_box.get("1.0", tk.END)
            new_content = content.replace(link_ref + " ", "", 1)
            if new_content == content:
                new_content = content.replace(link_ref, "", 1)
            self.input_box.delete("1.0", tk.END)
            self.input_box.insert("1.0", new_content.rstrip("\n"))

    def clear_attachments(self):
        for att in list(self.attachments):
            self.remove_attachment(att)

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
        self.canvas.tag_lower("bg")
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
        self.entries_text.insert(tk.END, "Loading...")
        self.entries_text.configure(state=tk.DISABLED)
        self.entries_text.see(tk.END)

        def fetch_task():
            text = get_last_entries()
            self.root.after(0, self._update_entries_text, text)
            
        threading.Thread(target=fetch_task, daemon=True).start()

    def _update_entries_text(self, text):
        self.entries_text.configure(state=tk.NORMAL)
        self.entries_text.delete("1.0", tk.END)
        self.entries_text.insert(tk.END, text)
        self.entries_text.configure(state=tk.DISABLED)
        self.entries_text.see(tk.END)

    def show(self):
        logging.info("Show triggered.")
        if self.is_expanded:
            self.toggle_history()
        self.input_box.delete("1.0", tk.END)
        self.clear_attachments()
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
        
        # Snapshot attachment data before hiding (must read tk vars on main thread)
        attachment_data = []
        for att in self.attachments:
            attachment_data.append({
                "data": att["data"],
                "is_clipboard": att["is_clipboard"],
                "user_name": att["name_var"].get().strip(),
                "link_ref": att.get("link_ref", ""),
            })

        if text or attachment_data:
            self.hide()
            threading.Thread(
                target=self._submit_entry, args=(text, attachment_data), daemon=True
            ).start()
        return "break"

    def _submit_entry(self, text, attachment_data):
        try:
            if attachment_data:
                media_path = self.get_jrnl_media_path()
                if not media_path:
                    logging.error("Could not determine jrnl media path")
                else:
                    for att in attachment_data:
                        if att["is_clipboard"]:
                            img = att["data"]
                            dest_filename = f"{uuid.uuid4().hex[:8]}.png"
                            img.save(os.path.join(media_path, dest_filename))
                        else:
                            src_path = att["data"]
                            dest_filename = os.path.basename(src_path)
                            dest_path = os.path.join(media_path, dest_filename)
                            # Avoid overwriting existing files by appending a short suffix
                            if os.path.exists(dest_path):
                                name, ext = os.path.splitext(dest_filename)
                                dest_filename = f"{name}_{uuid.uuid4().hex[:6]}{ext}"
                                dest_path = os.path.join(media_path, dest_filename)
                            shutil.copy2(src_path, dest_path)
                        user_name = att["user_name"]
                        if not user_name:
                            user_name = dest_filename
                        
                        proper_link = f"[{user_name}](jrnl-media/{dest_filename})"
                        link_ref = att.get("link_ref", "")
                        if link_ref and link_ref in text:
                            text = text.replace(link_ref, proper_link, 1)
                        else:
                            text += f"\n{proper_link}"

            if text:
                add_entry(text)
        except Exception as e:
            logging.error(f"Error submitting entry: {e}")

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
    hotkey = os.environ.get("JRNL_HOTKEY", "<cmd>+j")
    try:
        logging.info(f"Starting hotkey listener for {hotkey}...")
        with keyboard.GlobalHotKeys({hotkey: on_hotkey}) as h:
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
