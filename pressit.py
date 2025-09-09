import tkinter as tk
from tkinter import messagebox
from pynput.keyboard import Key, Controller as KeyboardController, Listener, KeyCode
from pynput.mouse import Controller as MouseController, Button
import threading
import time
import sys

keyboard = KeyboardController()
mouse = MouseController()

class KeyPresserCPS:
    def __init__(self, master):
        self.master = master
        master.title("Key/Mouse Presser - CPS Mode")
        master.geometry("400x250")
        master.config(bg="#1a1a1a")

        # Key input
        tk.Label(master, text="Key to Press (type 'Click' for mouse):", bg="#1a1a1a", fg="lime", font=("Arial", 12, "bold")).pack(pady=5)
        self.key_entry = tk.Entry(master)
        self.key_entry.pack(pady=5)
        self.key_entry.insert(0, "space")

        # CPS input
        tk.Label(master, text="CPS (Clicks Per Second, -1 for hold):", bg="#1a1a1a", fg="cyan", font=("Arial", 10, "bold")).pack(pady=5)
        self.cps_entry = tk.Entry(master)
        self.cps_entry.pack(pady=5)
        self.cps_entry.insert(0, "1000")

        # Footer with supported keys
        tk.Label(master, text="Supported special keys: space, enter, shift, ctrl, alt, tab, backspace, esc, arrows (up/down/left/right), or any character", 
                 bg="#1a1a1a", fg="white", wraplength=380, font=("Arial", 8)).pack(pady=10)

        tk.Label(master, text="Right Shift: Toggle | / + Right Shift: Exit", bg="#1a1a1a", fg="white").pack(pady=5)

        self.running = False
        self.toggle_lock = False
        self.pressed_keys = set()
        self.interval = 0.001
        self.current_key = ""

        # Status window
        self.status_win = tk.Toplevel(master)
        self.status_win.title("Presser Status")
        self.status_win.geometry("250x80")
        self.status_win.config(bg="#111111")
        self.status_label = tk.Label(self.status_win, text="Idle", fg="lime", bg="#111111", font=("Arial", 12))
        self.status_label.pack(expand=True)

        threading.Thread(target=self.start_listener, daemon=True).start()
        threading.Thread(target=self.update_status, daemon=True).start()

    # Listener for hotkeys
    def start_listener(self):
        with Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()

    def on_press(self, key):
        self.pressed_keys.add(key)

        # Exit hotkey: / + Right Shift
        if Key.shift_r in self.pressed_keys and KeyCode.from_char('/') in self.pressed_keys:
            print("Exit hotkey pressed. Exiting...")
            self.running = False
            self.master.destroy()
            sys.exit()

        # Toggle key presser with Right Shift
        if key == Key.shift_r and not self.toggle_lock:
            self.toggle_lock = True
            threading.Thread(target=self.toggle_presser, daemon=True).start()

    def on_release(self, key):
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)
        if key == Key.shift_r:
            self.toggle_lock = False

    def toggle_presser(self):
        time.sleep(0.5)  # debounce
        if not self.running:
            # Read CPS
            try:
                cps = float(self.cps_entry.get())
                if cps == -1:
                    self.interval = -1
                else:
                    if cps <= 0:
                        raise ValueError
                    self.interval = 1.0 / cps
            except ValueError:
                messagebox.showerror("Error", "Enter a valid CPS number or -1 for hold.")
                self.toggle_lock = False
                return

            # Get key/mouse
            self.current_key = self.key_entry.get().strip().lower()
            self.running = True
            threading.Thread(target=self.press_loop, daemon=True).start()
            print("Presser started.")
        else:
            self.running = False
            print("Presser stopped.")
        self.toggle_lock = False

    # Update status window
    def update_status(self):
        while True:
            if self.running:
                self.status_label.config(text=f"Pressing: {self.current_key}\nCPS: {1/self.interval if self.interval>0 else 'Hold'}")
            else:
                self.status_label.config(text="Idle")
            time.sleep(0.1)

    # Press loop
    def press_loop(self):
        next_time = time.perf_counter()
        if self.interval == -1:
            if self.current_key == "click":
                self.press_mouse(hold=True)
            else:
                self.press_key(self.current_key, hold=True)
        else:
            while self.running:
                now = time.perf_counter()
                if now >= next_time:
                    if self.current_key == "click":
                        self.press_mouse()
                    else:
                        self.press_key(self.current_key)
                    next_time += self.interval
                else:
                    time.sleep(min(self.interval/10, 0.0005))

    # Press a key
    def press_key(self, key_str, hold=False):
        special_keys = {
            "space": Key.space,
            "enter": Key.enter,
            "shift": Key.shift,
            "ctrl": Key.ctrl,
            "alt": Key.alt,
            "tab": Key.tab,
            "backspace": Key.backspace,
            "esc": Key.esc,
            "up": Key.up,
            "down": Key.down,
            "left": Key.left,
            "right": Key.right
        }
        key_to_press = special_keys.get(key_str, key_str)
        if hold:
            keyboard.press(key_to_press)
            while self.running:
                time.sleep(0.001)
            keyboard.release(key_to_press)
        else:
            keyboard.press(key_to_press)
            keyboard.release(key_to_press)

    # Press mouse click
    def press_mouse(self, hold=False):
        if hold:
            mouse.press(Button.left)
            while self.running:
                time.sleep(0.001)
            mouse.release(Button.left)
        else:
            mouse.press(Button.left)
            mouse.release(Button.left)

if __name__ == "__main__":
    root = tk.Tk()
    app = KeyPresserCPS(root)
    root.mainloop()
