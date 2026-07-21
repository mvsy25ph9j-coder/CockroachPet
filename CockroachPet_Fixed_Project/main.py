import os
import sys
import time
import random
import math
import traceback
import tkinter as tk
from PIL import Image, ImageTk

APP_NAME = "CockroachPet"

def resource_path(relative):
    """Works both in normal Python and PyInstaller --onefile builds."""
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative)

def write_error(exc):
    try:
        folder = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(folder, "error.log"), "w", encoding="utf-8") as f:
            f.write("CockroachPet startup/runtime error\\n\\n")
            traceback.print_exc(file=f)
            f.write("\\n\\nException: " + repr(exc))
    except Exception:
        pass

class CockroachPet:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#010101")
        try:
            self.root.wm_attributes("-transparentcolor", "#010101")
        except tk.TclError:
            pass

        self.canvas = tk.Canvas(
            root, bg="#010101", highlightthickness=0,
            bd=0, relief="flat"
        )
        self.canvas.pack()

        self.original = Image.open(resource_path("assets/cockroach.png")).convert("RGBA")
        self.scale = 0.48
        self.facing = random.choice([-1, 1])
        self.vx = self.facing * random.uniform(1.0, 2.2)
        self.vy = random.uniform(-0.25, 0.25)
        self.target_speed = abs(self.vx)
        self.paused = False
        self.dragging = False
        self.state = "walk"
        self.state_end = time.time() + 2
        self.t = 0
        self.last_mouse_escape = 0
        self.last_click = 0

        self.render()

        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        self.x = random.randint(20, max(20, sw - self.w - 20))
        self.y = random.randint(60, max(60, sh - self.h - 80))
        self.move_window()

        self.canvas.bind("<ButtonPress-1>", self.press)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<ButtonRelease-1>", self.release)
        self.canvas.bind("<Button-3>", self.popup)
        self.root.bind("<Escape>", lambda e: self.root.destroy())

        self.menu = tk.Menu(root, tearoff=False)
        self.menu.add_command(label="暂停 / 继续", command=self.toggle_pause)
        self.menu.add_command(label="随机移动", command=self.teleport)
        self.menu.add_command(label="改变速度", command=self.change_speed)
        self.menu.add_separator()
        self.menu.add_command(label="退出", command=self.root.destroy)

        self.root.after(35, self.tick)

    def render(self):
        img = self.original.resize(
            (max(30, int(self.original.width*self.scale)),
             max(30, int(self.original.height*self.scale))),
            Image.Resampling.LANCZOS
        )
        if self.facing < 0:
            img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        # Subtle body bobbing during movement.
        if self.state == "walk":
            bob = int(math.sin(self.t * 0.75) * 1.3)
            if bob:
                layer = Image.new("RGBA", (img.width, img.height + 4), (0,0,0,0))
                layer.alpha_composite(img, (0, max(0, bob)))
                img = layer.crop((0, 0, img.width, img.height))

        self.photo = ImageTk.PhotoImage(img)
        self.w, self.h = img.size
        self.canvas.config(width=self.w, height=self.h)
        self.canvas.delete("all")
        self.canvas.create_image(self.w//2, self.h//2, image=self.photo)

    def move_window(self):
        self.root.geometry(f"+{int(self.x)}+{int(self.y)}")

    def set_state(self, name, seconds):
        self.state = name
        self.state_end = time.time() + seconds

    def press(self, e):
        self.dragging = True
        self.dx = e.x
        self.dy = e.y
        self.vx = self.vy = 0
        now = time.time()
        if now - self.last_click < 0.4:
            self.flee(self.root.winfo_pointerx(), self.root.winfo_pointery(), force=True)
        else:
            self.set_state("startle", 0.25)
        self.last_click = now

    def drag(self, e):
        if self.dragging:
            self.x = self.root.winfo_x() + e.x - self.dx
            self.y = self.root.winfo_y() + e.y - self.dy
            self.move_window()

    def release(self, e):
        self.dragging = False
        self.facing = random.choice([-1, 1])
        self.target_speed = random.uniform(1.3, 2.7)
        self.vx = self.facing * self.target_speed
        self.vy = random.uniform(-0.3, 0.3)
        self.set_state("run", 0.8)

    def popup(self, e):
        try:
            self.menu.tk_popup(e.x_root, e.y_root)
        finally:
            self.menu.grab_release()

    def toggle_pause(self):
        self.paused = not self.paused

    def change_speed(self):
        self.target_speed = random.choice([0.8, 1.5, 2.3, 3.5, 5.0])
        self.vx = self.facing * self.target_speed

    def teleport(self):
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.x = random.randint(0, max(0, sw-self.w))
        self.y = random.randint(30, max(30, sh-self.h))
        self.set_state("startle", 0.3)
        self.move_window()

    def flee(self, mx, my, force=False):
        now = time.time()
        if not force and now < self.last_mouse_escape + 1.2:
            return
        self.last_mouse_escape = now
        cx, cy = self.x + self.w/2, self.y + self.h/2
        dx, dy = cx-mx, cy-my
        d = max(1.0, math.hypot(dx,dy))
        self.facing = 1 if dx >= 0 else -1
        self.vx = dx/d * random.uniform(5.5, 9.0)
        self.vy = dy/d * random.uniform(3.0, 6.0)
        self.set_state("run", 1.3)

    def mouse_near(self):
        try:
            mx, my = self.root.winfo_pointerx(), self.root.winfo_pointery()
            cx, cy = self.x+self.w/2, self.y+self.h/2
            if math.hypot(mx-cx, my-cy) < max(self.w, self.h)*0.85:
                self.flee(mx, my)
        except tk.TclError:
            pass

    def tick(self):
        try:
            self.t += 1
            now = time.time()
            if not self.paused and not self.dragging:
                self.mouse_near()

                if self.state in ("run", "startle") and now >= self.state_end:
                    self.set_state("walk", random.uniform(1.5, 4.0))
                    self.target_speed = random.uniform(1.0, 2.4)

                # Smooth speed changes.
                speed = abs(self.vx)
                if speed < self.target_speed:
                    speed += 0.07
                elif speed > self.target_speed:
                    speed -= 0.05
                speed = max(0.25, speed)
                self.vx = self.facing * speed

                if self.state == "walk":
                    self.vy += math.sin(self.t * 0.11) * 0.012
                    self.vy *= 0.98

                sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()

                if self.x <= 0:
                    self.x = 0
                    self.facing = 1
                elif self.x + self.w >= sw:
                    self.x = sw - self.w
                    self.facing = -1

                if self.y <= 25:
                    self.y = 25
                    self.vy = abs(self.vy) + 0.2
                elif self.y + self.h >= sh:
                    self.y = sh - self.h
                    self.vy = -abs(self.vy) - 0.2

                # Occasional pause.
                if self.state == "walk" and random.random() < 0.0018:
                    self.set_state("idle", random.uniform(0.4, 1.2))
                    self.vx *= 0.1
                    self.vy *= 0.1
                elif self.state == "idle" and now >= self.state_end:
                    self.set_state("walk", 2)
                    self.facing = random.choice([-1,1])
                    self.target_speed = random.uniform(1.0, 2.5)

                self.x += self.vx
                self.y += self.vy
                self.move_window()

                if self.t % 3 == 0:
                    self.render()

            self.root.after(35, self.tick)
        except Exception as exc:
            write_error(exc)
            self.root.after(500, self.tick)

def main():
    root = tk.Tk()
    app = CockroachPet(root)
    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        write_error(exc)
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, "蟑螂桌面宠物启动失败。\\n请查看程序目录中的 error.log。", "CockroachPet", 0x10)
        except Exception:
            pass
