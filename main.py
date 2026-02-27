#!/usr/bin/env python3
import asyncio
import datetime
import os
import sys
from dotenv import load_dotenv
from today_vn_news.scraper import scrape_and_save
from today_vn_news.translator import translate_and_save
from today_vn_news.translator import translate_all_sources_parallel, save_translated_yaml, translate_weather_condition
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

    # 데이터 디렉토리 설정
    data_dir = "data"

    # 기본 대상일 설정
    if len(sys.argv) > 1:
        # 명령줄 인자로 날짜 지정 시 (YYMMDD 또는 YYMMDD-HHMM 형식 모두 지원)
        yymmdd_hhmm = sys.argv[1]
    else:
        # 인자 없이 실행 시 현재 시각으로 자동 생성 (YYYYMMDD_HHMM)
        yymmdd_hhmm = datetime.datetime.now().strftime("%Y%m%d_%H%M")

    # 기준일 설정 (ISO 형식)
    today_iso = datetime.datetime.now().strftime("%Y-%m-%d")
    today_display = datetime.datetime.now().strftime("%Y년 %m월 %d일 %H:%M")

    yaml_path = f"{data_dir}/{yymmdd_hhmm}.yaml"
    mov_path = f"{data_dir}/{yymmdd_hhmm}.mov"
    mp4_path = f"{data_dir}/{yymmdd_hhmm}.mp4"
    mp3_path = f"{data_dir}/{yymmdd_hhmm}.mp3"
    final_video = f"{data_dir}/{yymmdd_hhmm}_final.mp4"

    # 1. 스크래핑
    print("\n[*] 1단계: 뉴스 스크래핑 시작...")
    raw_yaml_path = f"{data_dir}/{yymmdd_hhmm}_raw.yaml"
    scraped_data = scrape_and_save(today_iso, raw_yaml_path)

    # 2. 번역 (비동기 병렬 처리)
    print("\n[*] 2단계: 뉴스 번역 시작 (병렬 처리)...")

    # 안전 및 기상 관제는 별도 처리
    safety_section = None
    if "안전 및 기상 관제" in scraped_data:
        safety_items = []
        for item in scraped_data["안전 및 기상 관제"]:
            if item.get("name") == "기상":
                condition = item.get("condition", "")
                translated_condition = translate_weather_condition(condition)
                temp = item.get("temp", "")
                humidity = item.get("humidity", "")
                content = f"{translated_condition}, 온도 {temp}, 습도 {humidity}"
                safety_items.append({
                    "title": f"기상 (NCHMF)",
                    "content": content,
                    "url": item["url"]
                })
            elif item.get("name") == "공기":
                safety_items.append({
                    "title": f"공기질 (IQAir) - AQI {item.get('aqi', '')}",
                    "content": item["content"],
                    "url": item["url"]
                })
            elif item.get("name") == "지진":
                safety_items.append({
                    "title": item["title"],
                    "content": item["content"],
                    "url": item["url"]
                })

        if safety_items:
            safety_section = {
                "id": "1",
                "name": "안전 및 기상 관제",
                "priority": "P0",
                "items": safety_items
            }

    # 병렬 번역 실행
    translated_sections = await translate_all_sources_parallel(scraped_data, today_display)

    # 안전 및 기상 관제를 맨 앞에 추가
    if safety_section:
        translated_sections.insert(0, safety_section)

    # YAML 저장
    if not translated_sections:
        print("\n[!] 2단계: 번역된 뉴스가 없어 파이프라인을 중단합니다.")
        sys.exit(1)

    yaml_data = {"sections": translated_sections}
    if not save_translated_yaml(yaml_data, today_display, yaml_path):
        print("\n[!] 2단계: YAML 저장 실패로 파이프라인을 중단합니다.")
        sys.exit(1)

    print(f"\n[+] 번역 완료: {len(translated_sections)}개 섹션")

    # 3. TTS 음성 변환 (항상 실행)
    print("\n[*] 3단계: TTS 음성 변환 시작...")
    await yaml_to_tts(yaml_path)

    # 4. 영상 합성 (항상 실행)
    default_bg = "assets/default_bg.png"
    if (
        os.path.exists(mov_path)
        or os.path.exists(mp4_path)
        or os.path.exists(default_bg)
    ):
        print("\n[*] 4단계: 영상 합성(FFmpeg) 시작...")
        synthesize_video(yymmdd_hhmm, data_dir)
    else:
        print(
            f"\n[!] 4단계: 베이스 영상(.mov, .mp4) 또는 기본 배경 이미지({default_bg})가 없어 합성을 건너뜁니다."
        )

    # 5. 유튜브 업로드 (항상 실행)
    if os.path.exists(final_video):
        print("\n[*] 5단계: 유튜브 업로드 시작...")
        success = upload_video(yymmdd_hhmm, data_dir)
        if success:
            print("\n🎉 모든 파이프라인 작업이 성공적으로 완료되었습니다!")
        else:
            print("\n⚠️ 유튜브 업로드 단계에서 문제가 발생했습니다.")
    else:
        print("\n[!] 5단계: 업로드할 최종 영상이 없어 종료합니다.")

    print("=" * 40)


if __name__ == "__main__":
    asyncio.run(main())
