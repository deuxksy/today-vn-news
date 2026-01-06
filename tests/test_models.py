import os
from dotenv import load_dotenv
import subprocess

load_dotenv()

models = ["gemini-1.5-flash", "gemini-2.0-flash-exp", "gemini-1.5-pro"]

for model in models:
    print(f"Testing model: {model}...")
    try:
        res = subprocess.run(["gemini", "Hello", "--model", model], capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            print(f"  [SUCCESS] {model} works!")
        else:
            print(f"  [FAIL] {model} failed. Stderr: {res.stderr[:200]}...")
    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] {model} timed out.")
    except Exception as e:
        print(f"  [ERROR] {model}: {e}")
