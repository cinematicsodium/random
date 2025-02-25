from datetime import datetime
import pyautogui
from time import sleep


def print_current_time(text=None):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = current_time if text is None else f"{current_time} - {text}"
    print(message)


def start_timer():
    for _ in range(4):
        sleep(60)
        print_current_time()
    sleep(60)


def typewriter():
    print_current_time("starting timer...")
    while True:
        start_timer()
        pyautogui.typewrite("x")
        print_current_time("x")


try:
    typewriter()
except Exception as e:
    print(f"error: {e}")
