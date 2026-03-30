#!/usr/bin/env python3
import asyncio
import datetime
import os
import sys
from dotenv import load_dotenv
from today_vn_news.scraper import scrape_and_save
from today_vn_news.translator import (
    translate_and_save,
    translate_all_sources_parallel,
    save_translated_yaml,
    translate_weather_condition,
)
from today_vn_news.tts import yaml_to_tts, TTSEngine
from today_vn_news.engine import synthesize_video
from today_vn_news.uploader import upload_video
from today_vn_news.video_source.resolver import VideoSourceResolver
from today_vn_news.video_source.archiver import MediaArchiver
from today_vn_news.config import VideoConfig
from today_vn_news.notifications.pipeline_status import (
    PipelineStatus,
    ALL_STEPS,
    STEP_SCRAPE,
    STEP_TRANSLATE,
    STEP_TTS,
    STEP_VIDEO,
    STEP_UPLOAD,
    STEP_ARCHIVE,
)
from today_vn_news.notifications.pushover import PushoverNotifier
from today_vn_news.timestamp import (
    normalize_timestamp,
    validate_yymmdd,
    exists_done,
    create_done,
    assert_exists_done,
)
from today_vn_news.exceptions import PipelineRestartError

# .env 파일 로드
load_dotenv()

# 로그 및 데이터 디렉토리 생성
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)


async def process_video_pipeline(
    yymmdd: str,
    data_dir: str,
    config: VideoConfig,
    status: PipelineStatus
) -> bool:
    """
    영상 파이프라인 처리: 소스 해결 → 합성 → 저장 → 업로드

    Args:
        yymmdd: YYMMDD 형식 타임스탬프 (6자리)
        data_dir: 데이터 디렉토리 경로
        config: 비디오 설정

    Returns:
        bool: 파이프라인 성공 여부
    """
    resolver = VideoSourceResolver(config)
    archiver = MediaArchiver(config)

    try:
        # 완료된 단계 건너뛰기 (engine)
        if exists_done(yymmdd, "engine"):
            print("[+] 4단계: 영상 합성 완료 파일이 존재합니다. 건너뜁니다.")
            # 완료된 영상 경로 확인
            local_final = f"{data_dir}/{yymmdd}_final.mp4"
            local_audio = f"{data_dir}/{yymmdd}.mp3"
            media_path_final = None

            # 3-1. MP3 음성 저장 (이미 완료되어 있을 가능성 높음)
            if os.path.exists(local_audio):
                try:
                    print("\n[*] Media에 MP3 음성 저장 중...")
                    audio_media_path = archiver.archive_audio(local_audio, yymmdd)
                    print(f"[+] Media MP3 저장 완료: {audio_media_path}")
                except Exception as e:
                    print(f"[!] Media MP3 저장 실패 (로컬 유지): {e}")

            # 3-2. MP4 영상 저장 (이미 완료되어 있을 가능성 높음)
            if os.path.exists(local_final):
                # 완료된 단계 건너뛰기
                if not exists_done(yymmdd, "archiver"):
                    try:
                        print("\n[*] Media에 영상 저장 중...")
                        media_path_final = archiver.archive(local_final, yymmdd)
                        print(f"[+] Media 저장 완료: {media_path_final}")
                        create_done(yymmdd, "archiver")
                        status.steps[STEP_ARCHIVE] = True
                    except Exception as e:
                        print(f"[!] Media 저장 실패 (로컬 유지): {e}")
                        # 저장 실패해도 로컬 파일은 있으므로 계속 진행
                else:
                    print("[+] Media 아카이빙 완료 파일이 존재합니다. 건너뜁니다.")
                    # 기존 Media 경로 로드 (resolver의 latest.mp4 확인)
                    media_path_final = archiver.resolve_existing(yymmdd)
                    if media_path_final:
                        print(f"[+] 기존 Media 경로 확인: {media_path_final}")

            # 4. 유튜브 업로드 (Media 이동 후 경로 우선, 없으면 로컬 파일 확인)
            upload_target = media_path_final if media_path_final and os.path.exists(media_path_final) else local_final

            if os.path.exists(upload_target):
                print("\n[*] 유튜브 업로드 시작...")

                # 완료된 단계 건너뛰기
                if not exists_done(yymmdd, "uploader"):
                    # Media 경로인 경우 data_dir 대신 Media 파일 직접 업로드
                    if media_path_final and os.path.exists(media_path_final):
                        video_id = upload_video(yymmdd, data_dir, video_path=str(media_path_final))
                    else:
                        video_id = upload_video(yymmdd, data_dir)

                    if video_id:
                        create_done(yymmdd, "uploader")
                        status.steps[STEP_UPLOAD] = True
                        status.youtube_url = f"https://youtube.com/watch?v={video_id}"
                else:
                    print("[+] 5단계: 유튜브 업로드 완료 파일이 존재합니다. 건너뜁니다.")
                    video_id = True  # 이미 업로드된 것으로 간주
                    status.steps[STEP_UPLOAD] = True

                return video_id
            else:
                print("\n[!] 업로드할 최종 영상이 없습니다.")
                return False
        else:
            # 선행 단계 확인
            assert_exists_done(yymmdd, "tts")

            # 1. 영상 소스 해결 (우선순위 체인)
            print("\n[*] 영상 소스 확인 중...")
            source_path, _ = resolver.resolve(yymmdd)

            # 2. 영상 합성 (source_path 전달)
            print("\n[*] 영상 합성 시작...")
            synthesize_video(
                base_name=yymmdd,
                data_dir=data_dir,
                source_path=str(source_path)
            )
            create_done(yymmdd, "engine")
            status.steps[STEP_VIDEO] = True

            # 3. Media에 저장 (최종 영상 및 음성 보존)
            local_final = f"{data_dir}/{yymmdd}_final.mp4"
            local_audio = f"{data_dir}/{yymmdd}.mp3"
            media_path_final = None  # Media 이동 후 경로 저장

            # 3-1. MP3 음성 저장
            if os.path.exists(local_audio):
                try:
                    print("\n[*] Media에 MP3 음성 저장 중...")
                    audio_media_path = archiver.archive_audio(local_audio, yymmdd)
                    print(f"[+] Media MP3 저장 완료: {audio_media_path}")
                except Exception as e:
                    print(f"[!] Media MP3 저장 실패 (로컬 유지): {e}")
                    # 저장 실패해도 로컬 파일은 있으므로 계속 진행

            # 3-2. MP4 영상 저장
            if os.path.exists(local_final):
                # 완료된 단계 건너뛰기
                if not exists_done(yymmdd, "archiver"):
                    try:
                        print("\n[*] Media에 영상 저장 중...")
                        media_path_final = archiver.archive(local_final, yymmdd)
                        print(f"[+] Media 저장 완료: {media_path_final}")
                        create_done(yymmdd, "archiver")
                        status.steps[STEP_ARCHIVE] = True
                    except Exception as e:
                        print(f"[!] Media 저장 실패 (로컬 유지): {e}")
                        # 저장 실패해도 로컬 파일은 있으므로 계속 진행
                else:
                    print("[+] Media 아카이빙 완료 파일이 존재합니다. 건너뜁니다.")
                    # 기존 Media 경로 로드 (resolver의 latest.mp4 확인)
                    media_path_final = archiver.resolve_existing(yymmdd)
                    if media_path_final:
                        print(f"[+] 기존 Media 경로 확인: {media_path_final}")

            # 4. 유튜브 업로드 (Media 이동 후 경로 우선, 없으면 로컬 파일 확인)
            upload_target = media_path_final if media_path_final and os.path.exists(media_path_final) else local_final

            if os.path.exists(upload_target):
                print("\n[*] 유튜브 업로드 시작...")

                # 완료된 단계 건너뛰기
                if not exists_done(yymmdd, "uploader"):
                    # Media 경로인 경우 data_dir 대신 Media 파일 직접 업로드
                    if media_path_final and os.path.exists(media_path_final):
                        video_id = upload_video(yymmdd, data_dir, video_path=str(media_path_final))
                    else:
                        video_id = upload_video(yymmdd, data_dir)

                    if video_id:
                        create_done(yymmdd, "uploader")
                        status.steps[STEP_UPLOAD] = True
                        status.youtube_url = f"https://youtube.com/watch?v={video_id}"
                else:
                    print("[+] 5단계: 유튜브 업로드 완료 파일이 존재합니다. 건너뜁니다.")
                    video_id = True  # 이미 업로드된 것으로 간주
                    status.steps[STEP_UPLOAD] = True

                return video_id
            else:
                print("\n[!] 업로드할 최종 영상이 없습니다.")
                return False

    except Exception as e:
        print(f"\n[!] 파이프라인 오류: {e}")
        return False

    finally:
        # 5. 임시 파일 정리 (보장)
        resolver.cleanup_temporary()


async def main():
    """
    🇻🇳 오늘의 베트남 뉴스 실행 엔트리포인트 (Full Pipeline)
    """
    print("=" * 40)
    print("🇻🇳 오늘의 베트남 뉴스 (today-vn-news)")
    print("=" * 40)

    # 데이터 디렉토리 설정
    data_dir = "data"

    # 파이프라인 상태 추적
    status = PipelineStatus()

    # 명령줄 인자 파싱
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--help", "-h"]:
            print("""
사용법:
  python main.py [날짜] [--tts=edge|qwen] [--voice=음성명] [--instruct="설명"] [--language=언어]

인자:
  날짜          처리할 날짜 (YYMMDD 형식, 생략 시 오늘 날짜)
  --tts         사용할 TTS 엔진 (edge 또는 qwen, 기본값: edge)
  --voice       TTS 음성
                - edge: ko-KR-SunHiNeural, ko-KR-BongJinNeural 등
                - qwen: Sohee, Vivian, Serena, Ryan, Aiden, Ono_Anna, Uncle_Fu, Dylan, Eric
  --language    언어 (Qwen3-TTS 만 사용, 기본값: Korean)
  --instruct    음성 스타일 설명 (Qwen3-TTS VoiceDesign 만 사용)
                예: "따뜻한 아나운서 음성", "밝은 여성 음성", "낮은 남성 음성"

예시:
  python main.py                        # 오늘 날짜, Edge TTS (기본)
  python main.py 260319                # 특정 날짜, Edge TTS (기본)
  python main.py --tts=qwen            # Qwen3-TTS 사용
  python main.py --tts=qwen --voice=Vivian  # Qwen3-TTS Vivian 음성
  python main.py --tts=qwen --voice=Sohee --instruct="따뜻한 아나운서 음성"
  python main.py --tts=qwen --voice=Ryan --language=English
            """)
            sys.exit(0)

        # 명령줄 인자로 날짜 지정 시 (YYMMDD 형식 지원)
        yymmdd_arg = None
        for arg in sys.argv[1:]:
            if not arg.startswith("--"):
                yymmdd_arg = arg
                break

        if yymmdd_arg:
            # 타임스탬프 정규화 및 검증
            yymmdd = normalize_timestamp(yymmdd_arg)
            validate_yymmdd(yymmdd)
        else:
            # 인자 없이 실행 시 오늘 날짜 사용 (YYMMDD)
            yymmdd = datetime.datetime.now().strftime("%y%m%d")
    else:
        # 인자 없이 실행 시 오늘 날짜 사용 (YYMMDD)
        yymmdd = datetime.datetime.now().strftime("%y%m%d")

    # TTS 엔진 선택 (환경 변수 또는 명령줄 인자)
    tts_engine_name = os.getenv("TTS_ENGINE", "edge").lower()
    tts_voice = None
    tts_language = "korean"
    tts_instruct = None

    # 명령줄 인자에서 TTS 엔진, 음성, 언어, instruct 파싱 (전체 인자 스캔)
    for arg in sys.argv[1:]:
        if arg.startswith("--tts="):
            tts_engine_name = arg.split("=")[1].lower()
        elif arg.startswith("--voice="):
            tts_voice = arg.split("=")[1]
        elif arg.startswith("--language="):
            tts_language = arg.split("=")[1]
        elif arg.startswith("--instruct="):
            tts_instruct = arg.split("=", 1)[1]  # = 이후 전체를 가져옴

    # TTS 엔진 설정
    if tts_engine_name == "qwen":
        tts_engine = TTSEngine.QWEN
        tts_voice = tts_voice or "Sohee"
        print(f"\n📢 TTS 엔진: Qwen3-TTS (로컬) - Voice: {tts_voice}")
        if tts_instruct:
            print(f"   Instruct: {tts_instruct}")
    else:
        tts_engine = TTSEngine.EDGE
        tts_voice = tts_voice or "ko-KR-SunHiNeural"
        print(f"\n📢 TTS 엔진: Edge TTS (클라우드) - Voice: {tts_voice}")

    # 비디오 설정 로딩 (YAML에서 Media 경로 등 가져오기)
    config = VideoConfig.from_yaml()
    print(f"\n📹 Media 경로: {config.media_mount_path}")

    # 기준일 설정 (ISO 형식)
    today_iso = datetime.datetime.now().strftime("%Y-%m-%d")
    today_display = datetime.datetime.now().strftime("%Y년 %m월 %d일")

    yaml_path = f"{data_dir}/{yymmdd}.yaml"

    try:
        # 1. 스크래핑
        print("\n[*] 1단계: 뉴스 스크래핑 시작...")

        # 완료된 단계 건너뛰기
        if exists_done(yymmdd, "scraper"):
            print("[+] 1단계: 스크래핑 완료 파일이 존재합니다. 건너뜁니다.")
            # 기존 스크래핑 결과 로드
            raw_yaml_path = f"{data_dir}/{yymmdd}_raw.yaml"
            from today_vn_news.translator import load_yaml
            scraped_data = load_yaml(raw_yaml_path)
        else:
            raw_yaml_path = f"{data_dir}/{yymmdd}_raw.yaml"
            scraped_data = scrape_and_save(today_iso, raw_yaml_path)
            create_done(yymmdd, "scraper")
            status.steps[STEP_SCRAPE] = True

        # 2. 번역 (비동기 병렬 처리)
        print("\n[*] 2단계: 뉴스 번역 시작 (병렬 처리)...")

        # 완료된 단계 건너뛰기
        if exists_done(yymmdd, "translator"):
            print("[+] 2단계: 번역 완료 파일이 존재합니다. 건너뜁니다.")
            # 기존 번역 결과 로드
            from today_vn_news.translator import load_yaml
            translated_sections = load_yaml(yaml_path)
        else:
            # 선행 단계 확인
            assert_exists_done(yymmdd, "scraper")

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
                raise RuntimeError("번역된 뉴스가 없습니다")

            yaml_data = {"sections": translated_sections}
            if not save_translated_yaml(yaml_data, today_display, yaml_path):
                print("\n[!] 2단계: YAML 저장 실패로 파이프라인을 중단합니다.")
                raise RuntimeError("YAML 저장 실패")

            print(f"\n[+] 번역 완료: {len(translated_sections)}개 섹션")
            create_done(yymmdd, "translator")
            status.steps[STEP_TRANSLATE] = True

        # 3. TTS 음성 변환 (항상 실행)
        print("\n[*] 3단계: TTS 음성 변환 시작...")

        # 완료된 단계 건너뛰기
        if exists_done(yymmdd, "tts"):
            print("[+] 3단계: TTS 완료 파일이 존재합니다. 건너뜁니다.")
        else:
            # 선행 단계 확인
            assert_exists_done(yymmdd, "translator")

            await yaml_to_tts(yaml_path, engine=tts_engine, voice=tts_voice, language=tts_language, instruct=tts_instruct)
            create_done(yymmdd, "tts")
            status.steps[STEP_TTS] = True

        # 4-5. 영상 파이프라인 (소스 해결 → 합성 → 저장 → 업로드)
        success = await process_video_pipeline(
            yymmdd=yymmdd,
            data_dir=data_dir,
            config=config,
            status=status  # PipelineStatus 전달
        )

        if success:
            print("\n🎉 모든 파이프라인 작업이 성공적으로 완료되었습니다!")
        else:
            print("\n⚠️ 파이프라인 작업에서 문제가 발생했습니다.")

    except Exception as e:
        # 마지막 완료된 단계 다음이 현재 실패 단계
        current_step = "unknown"
        completed = status.completed_steps
        if completed:
            # 완료된 단계 중 가장 마지막 단계 찾기
            last_completed_idx = ALL_STEPS.index(completed[-1])
            if last_completed_idx + 1 < len(ALL_STEPS):
                current_step = ALL_STEPS[last_completed_idx + 1]
        else:
            # 완료된 단계가 없으면 첫 번째 단계가 실패
            current_step = ALL_STEPS[0] if ALL_STEPS else "unknown"

        status.errors[current_step] = str(e)
        print(f"\n[!] 파이프라인 오류: {e}")

    finally:
        # 7단계: Pushover 알림 (무조건 실행)
        notifier = PushoverNotifier.from_env_or_none()
        if notifier:
            print("\n[*] 알림 전송 중...")
            notifier.send_notification(status)

        print("=" * 40)


if __name__ == "__main__":
    asyncio.run(main())
