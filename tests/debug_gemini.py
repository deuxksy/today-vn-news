import os
from dotenv import load_dotenv
import subprocess

load_dotenv()

if "GEMINI_API_KEY" in os.environ and "GOOGLE_API_KEY" not in os.environ:
    print("Mapping GEMINI_API_KEY to GOOGLE_API_KEY")
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

google_key = os.getenv("GOOGLE_API_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")
print(f"GOOGLE_API_KEY: {google_key}")
print(f"GEMINI_API_KEY: {gemini_key}")

print("Running Gemini API Health Check via curl (JSON)...")
try:
    # curl 명령어로 직접 API 호출 (최소 토큰 사용)
    # 1+1 계산 요청
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={google_key}"
    payload = '{"contents":[{"parts":[{"text":"1+1"}]}]}'
    
    res = subprocess.run(
        [
            "curl", "-s", "-X", "POST", api_url,
            "-H", "Content-Type: application/json",
            "-d", payload
        ],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    print("STDOUT:", res.stdout)
    if res.returncode == 0 and '"text":' in res.stdout:
        print("[SUCCESS] API responded with text generation.")
    else:
        print("[FAIL] API response invalid or error.")
        print("STDERR:", res.stderr)
    
    print("Return Code:", res.returncode)

except Exception as e:
    print(f"Error invoking curl: {e}")
