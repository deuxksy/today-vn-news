#!/usr/bin/env python3
import asyncio
import asyncio
import datetime
import os
import sys
from dotenv import load_dotenv
from today_vn_news.collector import fetch_all_news
from today_vn_news.tts import yaml_to_tts
from today_vn_news.engine import synthesize_video
from today_vn_news.uploader import upload_video

# .env 파일 로드
load_dotenv()

# 로그 및 데이터 디렉토리 생성
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

async def main():
    """
    🇻🇳 오늘의 베트남 뉴스 실행 엔트리포인트 (Full Pipeline)
    """
    print("=" * 40)
    print("🇻🇳 오늘의 베트남 뉴스 (today-vn-news)")
    print("=" * 40)
    
    # 기본 대상일 설정
    if len(sys.argv) > 1:
        # 명령줄 인자로 날짜 지정 시 (YYMMDD 또는 YYMMDD-HHMM 형식 모두 지원)
        yymmdd_hhmm = sys.argv[1]
    else:
        # 인자 없이 실행 시 현재 시각으로 자동 생성 (YYYYMMDD_HHMM)
        yymmdd_hhmm = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    
    yaml_path = f"data/{yymmdd_hhmm}.yaml"
    mov_path = f"data/{yymmdd_hhmm}.mov"
    mp4_path = f"data/{yymmdd_hhmm}.mp4"
    mp3_path = f"data/{yymmdd_hhmm}.mp3"
    final_video = f"data/{yymmdd_hhmm}_final.mp4"

    # 1. 뉴스 데이터 수집
    if not os.path.exists(yaml_path):
        print("[*] 1단계: 뉴스 데이터 수집 시작...")
        if not fetch_all_news(yymmdd_hhmm):
            print("\n[!] 1단계: 수집 실패로 인해 파이프라인을 중단합니다.")
            sys.exit(1)
    else:
        print(f"[*] 1단계: YAML 데이터가 이미 존재합니다. ({yaml_path})")
    
    # 수집 후 파일 존재 여부 재확인 (혹시 함수에서 True를 반환했지만 파일이 없을 경우 대비)
    if not os.path.exists(yaml_path):
        print(f"\n[!] 1단계: 결과 파일({yaml_path})이 없어 파이프라인을 중단합니다.")
        sys.exit(1)

    # 2. TTS 음성 변환 (MP3 생성)
    if not os.path.exists(mp3_path):
        print("\n[*] 2단계: TTS 음성 변환 시작...")
        await yaml_to_tts(yaml_path)
    else:
        print(f"\n[*] 2단계: 음성 파일이 이미 존재합니다. ({mp3_path})")

    # 3. 영상 합성 (MP4 생성)
    if not os.path.exists(final_video):
        default_bg = "assets/default_bg.png"
        if os.path.exists(mov_path) or os.path.exists(mp4_path) or os.path.exists(default_bg):
            print("\n[*] 3단계: 영상 합성(FFmpeg) 시작...")
            synthesize_video(yymmdd_hhmm)
        else:
            print(f"\n[!] 3단계: 베이스 영상(.mov, .mp4) 또는 기본 배경 이미지({default_bg})가 없어 합성을 건너뜁니다.")
    else:
        print(f"\n[*] 3단계: 최종 영상이 이미 존재합니다. ({final_video})")

    # 4. 유튜브 업로드
    if os.path.exists(final_video):
        print("\n[*] 4단계: 유튜브 업로드 시작...")
        success = upload_video(yymmdd_hhmm)
        if success:
            print("\n🎉 모든 파이프라인 작업이 성공적으로 완료되었습니다!")
        else:
            print("\n⚠️ 유튜브 업로드 단계에서 문제가 발생했습니다.")
    else:
        print("\n[!] 4단계: 업로드할 최종 영상이 없어 종료합니다.")



    print("=" * 40)

if __name__ == "__main__":
    asyncio.run(main())
