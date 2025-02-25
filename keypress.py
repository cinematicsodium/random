from datetime import datetime
import pyautogui
from time import sleep


def timeprint(text=None):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = current_time if text is None else f"{current_time} - {text}"
    print(message)


def start_timer():
    num_minutes = 5
    seconds_per_minute = 60
    for n in range(num_minutes):
        sleep(seconds_per_minute)
        if n == num_minutes - 1:
            return
        timeprint()


def keypress():
    print_current_time("starting timer...")
    while True:
        start_timer()
        pyautogui.typewrite("x")
        print_current_time("x")


try:
    keypress()
except Exception as e:
    print(f"error: {e}")
