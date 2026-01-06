import os
from dotenv import load_dotenv
import subprocess

load_dotenv()

if "GEMINI_API_KEY" in os.environ and "GOOGLE_API_KEY" not in os.environ:
    print("Mapping GEMINI_API_KEY to GOOGLE_API_KEY")
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

print("Running gemini command with timeout...")
try:
    res = subprocess.run(["gemini", "Hello"], capture_output=True, text=True, timeout=10)
    print("STDOUT:", res.stdout)
    print("STDERR:", res.stderr)
    print("Return Code:", res.returncode)
except subprocess.TimeoutExpired:
    print("Timed out!")
except Exception as e:
    print(f"Error running gemini: {e}")
