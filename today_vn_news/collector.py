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
        "추출 규칙 및 출력 포맷:\n"
        "- 이슈 2개로 제한.\n"
        "- 형식:\n"
        "### 제목\n\n"
        "- 한국어 3줄 요약 첫 번째 줄\n"
        "- 한국어 3줄 요약 두 번째 줄\n"
        "- 한국어 3줄 요약 세 번째 줄\n\n"
        "[원문 링크]\n\n"
        "**TTS(음성 합성) 최적화 주의사항:**\n"
        "1. 에모지(Emoji)나 특수 기호를 절대 사용하지 마세요.\n"
        "2. 괄호 안의 영어 표기나 불필요한 외래어 사용을 자제하고 순수 한국어로만 작성하세요.\n"
        "3. 문장은 읽기 자연스럽도록 명확하게 끝맺음 하세요."
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

        # 5. 파일 저장 및 헤더 관리
        is_new_file = not os.path.exists(output_path)
        file_mode = "a" if not is_new_file else "w"
        
        with open(output_path, file_mode, encoding="utf-8") as f:
            if is_new_file:
                # 파일 신규 생성 시 메인 헤더 추가 (날짜 형식: YYYY년 MM월 DD일)
                f.write(f"# 오늘의 베트남 주요 뉴스 ({now.strftime('%Y년 %m월 %d일')})\n\n")
            else:
                # 기존 파일에 추가 시 구분선 추가
                f.write("\n\n---\n\n")
            
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
