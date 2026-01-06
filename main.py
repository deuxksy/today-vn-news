#!/usr/bin/env python3
import asyncio
import datetime
import os
import sys
from dotenv import load_dotenv
from today_vn_news.collector import fetch_all_news
from today_vn_news.tts import md_to_tts
from today_vn_news.engine import synthesize_video
from today_vn_news.uploader import upload_video

# .env 파일 로드
load_dotenv()

async def main():
    """
    🇻🇳 오늘의 베트남 뉴스 실행 엔트리포인트 (Full Pipeline)
    """
    print("=" * 40)
    print("🇻🇳 오늘의 베트남 뉴스 (today-vn-news)")
    print("=" * 40)
    
    # 기본 대상일 설정
    if len(sys.argv) > 1:
        yymmdd = sys.argv[1]
    else:
        yymmdd = datetime.datetime.now().strftime("%y%m%d")
    
    md_path = f"data/{yymmdd}.md"
    mov_path = f"data/{yymmdd}.mov"
    mp3_path = f"data/{yymmdd}.mp3"
    final_video = f"data/{yymmdd}_final.mp4"

    # 1. 뉴스 데이터 수집
    if not os.path.exists(md_path):
        print("[*] 1단계: 뉴스 데이터 수집 시작...")
        fetch_all_news()
    else:
        print(f"[*] 1단계: 마크다운 데이터가 이미 존재합니다. ({md_path})")

    # 2. TTS 음성 변환 (MP3 생성)
    if not os.path.exists(mp3_path):
        print("\n[*] 2단계: TTS 음성 변환 시작...")
        await md_to_tts(md_path)
    else:
        print(f"\n[*] 2단계: 음성 파일이 이미 존재합니다. ({mp3_path})")

    # 3. 영상 합성 (MP4 생성)
    if not os.path.exists(final_video):
        if os.path.exists(mov_path):
            print("\n[*] 3단계: 영상 합성(FFmpeg) 시작...")
            synthesize_video(yymmdd)
        else:
            print(f"\n[!] 3단계: 베이스 영상({mov_path})이 없어 합성을 건너뜁니다.")
    else:
        print(f"\n[*] 3단계: 최종 영상이 이미 존재합니다. ({final_video})")

    # 4. 유튜브 업로드 (인증 완료 시까지 주석 처리)
    # 4. 유튜브 업로드
    if os.path.exists(final_video):
        print("\n[*] 4단계: 유튜브 업로드 시작...")
        success = upload_video(yymmdd)
        if success:
            print("\n🎉 모든 파이프라인 작업이 성공적으로 완료되었습니다!")
        else:
            print("\n⚠️ 유튜브 업로드 단계에서 문제가 발생했습니다.")
    else:
        print("\n[!] 4단계: 업로드할 최종 영상이 없어 종료합니다.")

    print("=" * 40)

if __name__ == "__main__":
    asyncio.run(main())
