#!/usr/bin/env python3
import asyncio
import datetime
import os
import sys
from today_vn_news.collector import fetch_it_news
from today_vn_news.tts import md_to_tts
from today_vn_news.engine import synthesize_video

async def main():
    """
    🇻🇳 오늘의 베트남 뉴스 실행 엔트리포인트 (Integrated MVP)
    """
    print("=" * 40)
    print("🇻🇳 오늘의 베트남 뉴스 (today-vn-news)")
    print("=" * 40)
    
    # 기본 대상일 설정 (인자가 있으면 사용, 없으면 오늘 날짜)
    if len(sys.argv) > 1:
        yymmdd = sys.argv[1]
    else:
        yymmdd = datetime.datetime.now().strftime("%y%m%d")
    
    md_path = f"data/{yymmdd}.md"
    mov_path = f"data/{yymmdd}.mov"

    # 1. 뉴스 데이터 수집
    if not os.path.exists(md_path):
        print("[*] 1단계: 뉴스 데이터 수집 시작...")
        fetch_it_news()
    else:
        print(f"[*] 1단계: 마크다운 데이터가 이미 존재합니다. ({md_path})")

    # 2. TTS 음성 변환 
    mp3_path = md_path.replace(".md", ".mp3")
    if not os.path.exists(mp3_path):
        print("\n[*] 2단계: TTS 음성 변환 시작...")
        await md_to_tts(md_path)
    else:
        print(f"\n[*] 2단계: 음성 파일이 이미 존재합니다. ({mp3_path})")

    # 3. 영상 합성 (MOV가 있는 경우에만 실행)
    if os.path.exists(mov_path):
        print("\n[*] 3단계: 영상 합성(FFmpeg) 시작...")
        synthesize_video(yymmdd)
    else:
        print(f"\n[!] 3단계: 베이스 영상({mov_path})이 없어 합성을 건너뜁니다.")
    
    print("\n" + "=" * 40)
    print(f"🎉 모든 작업 완료 (대상일: {yymmdd})")
    print("=" * 40)

if __name__ == "__main__":
    asyncio.run(main())
