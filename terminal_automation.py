"""Terminal interface for the local game automation scheduler."""

from __future__ import annotations

import threading
import time
import random

import pyautogui
from pynput import keyboard


DEFAULT_TARGET = (1580, 525)
PLAY_INTERVAL = 60


class TerminalAutomation:
    def __init__(self) -> None:
        self.target = DEFAULT_TARGET
        self.stop_event = threading.Event()
        self.worker: threading.Thread | None = None
        self.listener: keyboard.Listener | None = None
        self.lock = threading.Lock()
        self.play_clicks = 0
        self.other_actions = 0
        self.last_action = "None"

    def start_listener(self) -> None:
        self.listener = keyboard.Listener(on_press=self._on_key)
        self.listener.daemon = True
        self.listener.start()

    def _on_key(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        if key == keyboard.Key.esc:
            self.stop()
            print("\n[STOPPED] ESC pressed.")

    def select_target(self) -> None:
        print("Move the mouse over the Play Again button, then press Enter here.")
        input()
        position = pyautogui.position()
        self.target = (position.x, position.y)
        print(f"Target set to {self.target}.")

    def start(self) -> None:
        if self.worker and self.worker.is_alive():
            print("Already running.")
            return
        self.stop_event.clear()
        self.play_clicks = 0
        self.other_actions = 0
        self.last_action = "None"
        self.worker = threading.Thread(target=self._run_scheduler, daemon=True)
        self.worker.start()
        print("[STARTED] Play Again=1m | W every 10-15s | ESC=stop")

    def _run_scheduler(self) -> None:
        now = time.monotonic()
        next_play = now
        next_key = now + random.uniform(10, 15)
        try:
            while not self.stop_event.is_set():
                now = time.monotonic()
                if now >= next_play:
                    pyautogui.click(*self.target)
                    self.play_clicks += 1
                    self.last_action = "Play Again click"
                    print(f"\n[PLAY] Play Again click #{self.play_clicks}")
                    next_play += PLAY_INTERVAL
                if now >= next_key:
                    key = "w"
                    pyautogui.keyDown("w")
                    time.sleep(0.2)
                    pyautogui.keyUp("w")
                    self.other_actions += 1
                    self.last_action = f"Key {key.upper()}"
                    print(f"\n[KEY] {key.upper()}")
                    next_key = time.monotonic() + random.uniform(10, 15)
                wait_for = min(next_play, next_key) - time.monotonic()
                self.stop_event.wait(max(0.01, min(wait_for, 0.25)))
        except Exception as exc:
            print(f"\n[ERROR] {exc}")
            self.stop_event.set()

    def stop(self) -> None:
        self.stop_event.set()
        if self.worker and self.worker.is_alive() and threading.current_thread() is not self.worker:
            self.worker.join(timeout=0.25)
        print("[STOPPED]")

    def status(self) -> None:
        running = bool(self.worker and self.worker.is_alive() and not self.stop_event.is_set())
        print(
            f"Status: {'Running' if running else 'Stopped'} | Target: {self.target} | "
            f"Play Again: {self.play_clicks} | Other actions: {self.other_actions} | Last: {self.last_action}"
        )

    def run(self) -> None:
        self.start_listener()
        print("Local Game Automation")
        print("Commands: target | start | stop | status | quit")
        print(f"Default target: {self.target} (1920x1080 screenshot coordinates)")
        try:
            while True:
                command = input("> ").strip().lower()
                if command in {"target", "t"}:
                    self.select_target()
                elif command in {"start", "s"}:
                    self.start()
                elif command in {"stop", "x"}:
                    self.stop()
                elif command in {"status", "?"}:
                    self.status()
                elif command in {"quit", "q", "exit"}:
                    break
                elif command:
                    print("Unknown command. Use: target, start, stop, status, quit")
        except (KeyboardInterrupt, EOFError):
            print()
        finally:
            self.stop()
            if self.listener:
                self.listener.stop()


if __name__ == "__main__":
    pyautogui.PAUSE = 0.05
    pyautogui.FAILSAFE = True
    TerminalAutomation().run()
