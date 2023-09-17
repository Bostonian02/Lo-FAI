import os
import subprocess
import sys
from test import get_current_prompt

subprocess.Popen(["python3", r"C:\Users\saget\Desktop\Shellhacks2023\Lo-FAI\poll.py"])
subprocess.Popen(["python3", r"C:\Users\saget\Desktop\Shellhacks2023\Lo-FAI\test.py"])
subprocess.Popen(["python3", r"C:\Users\saget\Desktop\Shellhacks2023\Lo-FAI\imgWindow.py"])

user_input = None

while True:
    prev_input = user_input
    user_input = get_current_prompt()
    if (user_input == prev_input):
        continue
    os.system(f"python3 C:\\Users\\saget\\Desktop\\Shellhacks2023\\Lo-FAI\\SDimgGen.py '{user_input}'")