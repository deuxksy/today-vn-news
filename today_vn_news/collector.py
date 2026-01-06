#!/usr/bin/env python3
import subprocess
import datetime
import os
import sys

"""
IT 뉴스 수집 모듈 (Gemini CLI Wrapper)
- 목적: Gemini CLI를 활용한 베트남 IT 뉴스(ICTNews) 수집
- 상세 사양: ContextFile.md 7.1 참조
"""

def fetch_it_news():
    # 1. 날짜 정보 생성 (YYMMDD 및 YYYY-MM-DD)
    now = datetime.datetime.now()
    yymmdd = now.strftime("%y%m%d")
    today_full = now.strftime("%Y-%m-%d")
    
    data_dir = "data"
    output_path = os.path.join(data_dir, f"{yymmdd}.md")

    # 2. 데이터 디렉토리 확인
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # 3. Gemini CLI 프롬프트 구성
    # 데이터 소스: ICTNews (https://vietnamnet.vn/ict)
    prompt = (
        f"https://vietnamnet.vn/ict 에서 {today_full} 날짜의 베트남 IT 뉴스 중 가장 중요한 이슈 2개를 요약해줘.\n\n"
        "추출 규칙:\n"
        "- 이슈 2개로 제한.\n"
        "- 형식:\n"
        "### 제목\n\n"
        "- 한국어 3줄 요약 첫 번째 줄\n"
        "- 한국어 3줄 요약 두 번째 줄\n"
        "- 한국어 3줄 요약 세 번째 줄\n\n"
        "[원문 링크]\n\n"
        "주의: 반드시 한글 요약을 포함하고, 마크다운 ### 제목 스타일을 지켜줘."
    )

    print(f"[*] IT 뉴스 수집 시작... (대상일: {today_full})")

    try:
        # 4. Gemini CLI 실행
        # stdout을 캡처하여 파일에 기록
        process = subprocess.run(
            ["gemini", prompt],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )

        if process.returncode != 0:
            print(f"[!] Gemini CLI 실행 오류 (Return Code: {process.returncode})")
            print(f"Error Output: {process.stderr}")
            return False

        content = process.stdout.strip()
        if not content:
            print("[!] 수집된 뉴스 내용이 없습니다.")
            return False

        # 5. 파일 저장 (Append 모드)
        # 기존 파일이 있으면 하단에 추가, 없으면 새로 생성
        file_mode = "a" if os.path.exists(output_path) else "w"
        with open(output_path, file_mode, encoding="utf-8") as f:
            if file_mode == "a":
                f.write("\n\n---\n\n")  # 구분선 추가
            f.write(content)
            f.write("\n")

        print(f"[+] 뉴스 수집 및 저장 완료: {output_path}")
        return True

    except FileNotFoundError:
        print("[!] 'gemini' 명령어를 찾을 수 없습니다. CLI가 설치되어 있는지 확인해주세요.")
        return False
    except Exception as e:
        print(f"[!] 예기치 못한 오류 발생: {str(e)}")
        return False

if __name__ == "__main__":
    fetch_it_news()
