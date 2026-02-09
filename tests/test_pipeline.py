#!/usr/bin/env python3
"""
파이프라인 테스트 코드
- 각 단계별 테스트 실행
"""

import asyncio
import os
import sys
from pathlib import Path

# 프로젝트 루트 경로 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from today_vn_news.scraper import scrape_and_save
from today_vn_news.translator import translate_and_save
from today_vn_news.tts import yaml_to_tts
from today_vn_news.engine import synthesize_video
from today_vn_news.uploader import upload_video

# .env 파일 로드
load_dotenv()


async def test_step1_scraping():
    """
    1단계: 스크래핑 테스트
    """
    print("\n" + "=" * 50)
    print("[테스트] 1단계: 스크래핑 테스트")
    print("=" * 50)
    
    yymmdd_hhmm = "test_scraping"
    raw_yaml_path = f"data/{yymmdd_hhmm}_raw.yaml"
    
    try:
        scraped_data = scrape_and_save("2026-02-09", raw_yaml_path)
        print(f"\n[+] 스크래핑 성공!")
        print(f"[+] 원본 YAML: {raw_yaml_path}")
        return scraped_data
    except Exception as e:
        print(f"\n[!] 스크래핑 실패: {str(e)}")
        return None


async def test_step2_translation(scraped_data):
    """
    2단계: 번역 테스트
    """
    print("\n" + "=" * 50)
    print("[테스트] 2단계: 번역 테스트")
    print("=" * 50)
    
    if not scraped_data:
        print("\n[!] 스크래핑 데이터가 없어 번역 테스트를 건너뜁니다.")
        return False
    
    yymmdd_hhmm = "test_translation"
    yaml_path = f"data/{yymmdd_hhmm}.yaml"
    
    try:
        success = translate_and_save(scraped_data, "2026년 02월 09일 16:00", yaml_path)
        if success:
            print(f"\n[+] 번역 성공!")
            print(f"[+] 번역된 YAML: {yaml_path}")
        return success
    except Exception as e:
        print(f"\n[!] 번역 실패: {str(e)}")
        return False


async def test_step3_tts():
    """
    3단계: TTS 테스트
    """
    print("\n" + "=" * 50)
    print("[테스트] 3단계: TTS 테스트")
    print("=" * 50)
    
    yymmdd_hhmm = "test_tts"
    yaml_path = f"data/{yymmdd_hhmm}.yaml"
    mp3_path = f"data/{yymmdd_hhmm}.mp3"
    
    # 테스트용 YAML 파일 생성
    test_yaml_content = """metadata:
  date: 2026-02-09
  time: 16:00
  location: Ho Chi Minh City (Saigon Pearl)
sections:
  - id: "1"
    name: 테스트
    priority: P0
    items:
      - title: 테스트 제목
        content: 테스트 내용입니다.
        url: https://example.com
"""
    
    os.makedirs("data", exist_ok=True)
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(test_yaml_content)
    
    try:
        await yaml_to_tts(yaml_path)
        if os.path.exists(mp3_path):
            print(f"\n[+] TTS 성공!")
            print(f"[+] 생성된 MP3: {mp3_path}")
            return True
        else:
            print(f"\n[!] TTS 파일이 생성되지 않았습니다.")
            return False
    except Exception as e:
        print(f"\n[!] TTS 실패: {str(e)}")
        return False


def test_step4_video():
    """
    4단계: 영상 합성 테스트
    """
    print("\n" + "=" * 50)
    print("[테스트] 4단계: 영상 합성 테스트")
    print("=" * 50)
    
    yymmdd_hhmm = "test_video"
    mp3_path = f"data/{yymmdd_hhmm}.mp3"
    final_video = f"data/{yymmdd_hhmm}_final.mp4"
    
    # 테스트용 MP3 파일 생성 (더미)
    os.makedirs("data", exist_ok=True)
    with open(mp3_path, "wb") as f:
        f.write(b"TEST_MP3")
    
    try:
        synthesize_video(yymmdd_hhmm)
        if os.path.exists(final_video):
            print(f"\n[+] 영상 합성 성공!")
            print(f"[+] 생성된 영상: {final_video}")
            return True
        else:
            print(f"\n[!] 영상 파일이 생성되지 않았습니다.")
            return False
    except Exception as e:
        print(f"\n[!] 영상 합성 실패: {str(e)}")
        return False


def test_step5_upload():
    """
    5단계: 업로드 테스트
    """
    print("\n" + "=" * 50)
    print("[테스트] 5단계: 업로드 테스트")
    print("=" * 50)
    
    yymmdd_hhmm = "test_upload"
    
    try:
        success = upload_video(yymmdd_hhmm)
        if success:
            print(f"\n[+] 업로드 성공!")
        else:
            print(f"\n[!] 업로드 실패 (업로드할 파일이 없거나 업로드 실패)")
        return success
    except Exception as e:
        print(f"\n[!] 업로드 실패: {str(e)}")
        return False


async def run_all_tests():
    """
    모든 테스트 실행
    """
    print("=" * 50)
    print("🧪 파이프라인 테스트 시작")
    print("=" * 50)
    
    results = []
    
    # 1단계: 스크래핑
    scraped_data = await test_step1_scraping()
    results.append(("1. 스크래핑", scraped_data is not None))
    
    # 2단계: 번역
    translation_success = await test_step2_translation(scraped_data)
    results.append(("2. 번역", translation_success))
    
    # 3단계: TTS
    tts_success = await test_step3_tts()
    results.append(("3. TTS", tts_success))
    
    # 4단계: 영상 합성
    video_success = test_step4_video()
    results.append(("4. 영상 합성", video_success))
    
    # 5단계: 업로드
    upload_success = test_step5_upload()
    results.append(("5. 업로드", upload_success))
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약")
    print("=" * 50)
    
    for step, success in results:
        status = "[✅ 성공]" if success else "[❌ 실패]"
        print(f"{status} {step}")
    
    # 전체 성공 여부
    all_success = all(success for _, success in results)
    
    print("\n" + "=" * 50)
    if all_success:
        print("🎉 모든 테스트 성공!")
    else:
        print("⚠️ 일부 테스트가 실패했습니다.")
    print("=" * 50)


async def run_specific_test(step: str):
    """
    특정 단계 테스트 실행
    
    Args:
        step: 테스트할 단계 (1~5)
    """
    print("=" * 50)
    print(f"🧪 {step}단계 테스트 실행")
    print("=" * 50)
    
    if step == "1":
        await test_step1_scraping()
    elif step == "2":
        scraped_data = await test_step1_scraping()
        await test_step2_translation(scraped_data)
    elif step == "3":
        await test_step3_tts()
    elif step == "4":
        test_step4_video()
    elif step == "5":
        test_step5_upload()
    else:
        print("[!] 사용법: python tests/test_pipeline.py [단계번호]")
        print("    예: python tests/test_pipeline.py 1 (1단계만 테스트)")
        print("    예: python tests/test_pipeline.py all (모든 단계 테스트)")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        step = sys.argv[1].lower()
        
        if step == "all":
            asyncio.run(run_all_tests())
        elif step in ["1", "2", "3", "4", "5"]:
            asyncio.run(run_specific_test(step))
        else:
            print("[!] 잘못된 단계 번호입니다. 1~5 또는 'all'을 입력하세요.")
    else:
        print("=" * 50)
        print("🧪 파이프라인 테스트")
        print("=" * 50)
        print("\n사용법:")
        print("  python tests/test_pipeline.py all       - 모든 단계 테스트")
        print("  python tests/test_pipeline.py 1        - 1단계(스크래핑)만 테스트")
        print("  python tests/test_pipeline.py 2        - 2단계(번역)만 테스트")
        print("  python tests/test_pipeline.py 3        - 3단계(TTS)만 테스트")
        print("  python tests/test_pipeline.py 4        - 4단계(영상 합성)만 테스트")
        print("  python tests/test_pipeline.py 5        - 5단계(업로드)만 테스트")
        print("=" * 50)