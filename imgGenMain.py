import os
import subprocess
import sys

subprocess.Popen(["python3", r"C:\Users\saget\Desktop\Shellhacks2023\Lo-FAI\imgWindow.py"])

while True:
    user_input = input("Enter a prompt (or type 'exit' to quit): ")
    if user_input == 'exit':
        break
    os.system(f"python3 C:\\Users\\saget\\Desktop\\Shellhacks2023\\Lo-FAI\\SDimgGen.py '{user_input}'")