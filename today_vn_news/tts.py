#!/usr/bin/env python3
import asyncio
import edge_tts
import os
import re

"""
TTS 변환 모듈 (edge-tts Wrapper)
- 목적: 마크다운 파일의 텍스트를 추출하여 MP3 음성 파일로 변환
- 상세 사양: ContextFile.md 3.2 (기술 스택) 및 4장 (TTS 최적화 등) 참조
"""

async def generate_tts(text: str, output_path: str, voice: str = "ko-KR-SunHiNeural"):
    """
    텍스트를 음성 파일로 변환
    """
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def clean_markdown(md_text: str) -> str:
    """
    마크다운 문법 제거 (TTS 최적화)
    """
    # 1. 헤더 (###) 제거
    text = re.sub(r'#+\s*', '', md_text)
    # 2. 리스트 마커 (-) 제거
    text = re.sub(r'-\s*', '', text)
    # 3. 구분선 (---) 제거
    text = re.sub(r'---', '', text)
    # 4. 링크 ([제목](url)) 제거 - [원문 링크] 통째로 제거
    text = re.sub(r'\[원문 링크\]\(.*\)', '', text)
    # 5. 에모지 및 특수 유니코드 기호 제거
    text = re.sub(r'[^\w\s.,!가-힣]', '', text)
    # 6. 영어 약어 처리 (괄호 안의 영어 등 제거 - 선택 사항)
    # text = re.sub(r'\([a-zA-Z\s]+\)', '', text) 
    # 7. 불필요한 공백 및 빈 줄 정리
    text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
    
    return text

async def md_to_tts(md_path: str, voice: str = "ko-KR-SunHiNeural"):
    """
    MD 파일을 읽어서 동일한 경로에 mp3 생성
    """
    if not os.path.exists(md_path):
        print(f"[!] 파일을 찾을 수 없습니다: {md_path}")
        return

    print(f"[*] MD 파일 읽기 및 정제 시작: {md_path}")
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    cleaned_text = clean_markdown(md_content)
    
    # 출력 경로 설정 (YYMMDD.md -> YYMMDD.mp3)
    output_path = md_path.replace(".md", ".mp3")
    
    print(f"[*] TTS 변환 시작 (Voice: {voice})...")
    await generate_tts(cleaned_text, output_path, voice)
    print(f"[+] 음성 파일 생성 완료: {output_path}")

if __name__ == "__main__":
    # 임시 테스트 케이스 (필요 시 수정)
    import sys
    target_file = sys.argv[1] if len(sys.argv) > 1 else "data/260106.md"
    asyncio.run(md_to_tts(target_file))
