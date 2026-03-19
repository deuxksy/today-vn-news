#!/usr/bin/env python3
"""
TTS 변환 모듈 (Qwen3-TTS Rust CLI 래퍼)
- 목적: YAML 파일을 파싱하여 텍스트를 추출하고 qwen3-tts-rs CLI로 MP3 음성 파일로 변환
- 상세 사양: ContextFile.md 3.2 (기술 스택) 및 4 장 (TTS 최적화 등) 참조

qwen3-tts-rs CLI 사용:
- 설치: cargo install qwen_tts_cli --features metal,accelerate,audio-loading (macOS)
- 설치: cargo install qwen_tts_cli --features cuda,flash-attn,cudnn,nccl,audio-loading (Linux)
- GitHub: https://github.com/danielclough/qwen3-tts-rs
"""

import asyncio
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

from today_vn_news.logger import logger
from today_vn_news.exceptions import TTSError


# Qwen3-TTS 에서 사용 가능한 음성 목록
# 출처: https://github.com/danielclough/qwen3-tts-rs
# qwen3-tts-rs는 다음 프리미엄 음성을 지원합니다
AVAILABLE_VOICES = {
    # 한국어 음성
    "korean": {
        "Sohee": {"lang": "ko", "gender": "female", "desc": "Warm Korean female voice with rich emotion"},
    },
    # 영어 음성
    "english": {
        "Ryan": {"lang": "en", "gender": "male", "desc": "Dynamic male voice with strong rhythmic drive"},
        "Aiden": {"lang": "en", "gender": "male", "desc": "Sunny American male voice with a clear midrange"},
    },
    # 일본어 음성
    "japanese": {
        "Ono_Anna": {"lang": "ja", "gender": "female", "desc": "Playful Japanese female voice with a light, nimble timbre"},
    },
    # 중국어 음성 (기본)
    "chinese": {
        "Vivian": {"lang": "zh", "gender": "female", "desc": "Bright, slightly edgy young female voice"},
        "Serena": {"lang": "zh", "gender": "female", "desc": "Warm, gentle young female voice"},
        "Uncle_Fu": {"lang": "zh", "gender": "male", "desc": "Seasoned male voice with a low, mellow timbre"},
        "Dylan": {"lang": "zh", "gender": "male", "desc": "Youthful Beijing male voice with a clear, natural timbre"},
        "Eric": {"lang": "zh", "gender": "male", "desc": "Lively Chengdu male voice with a slightly husky brightness"},
    },
}


def list_available_voices(lang_filter: str = None):
    """
    사용 가능한 음성 목록 출력

    Args:
        lang_filter: 언어 필터 (ko, zh, en 등)
    """
    print("\n" + "=" * 80)
    print("🎤 Qwen3-TTS (qwen3-tts-rs CLI) 사용 가능한 음성 목록")
    print("=" * 80)
    print("\n💡 VoiceDesign 모드는 --instruct 옵션으로 음성 스타일을 지정할 수 있습니다.")
    print("=" * 80)

    for category, voices in AVAILABLE_VOICES.items():
        if lang_filter and category != lang_filter:
            if lang_filter not in ["ko", "zh", "en", "ja"]:
                continue

        print(f"\n📁 {category.upper()} 카테고리")
        print("-" * 80)
        print(f"{'음성명':<20} {'언어':<10} {'성별':<10} {'설명':<40}")
        print("-" * 80)

        for voice_name, info in voices.items():
            print(f"{voice_name:<20} {info['lang']:<10} {info['gender']:<10} {info['desc']:<40}")

    print("\n" + "=" * 80)
    print("💡 사용법:")
    print("   python main.py --tts=qwen --voice Sohee")
    print("   python main.py --tts=qwen --voice Sohee --instruct '따뜻한 아나운서 음성'")
    print("=" * 80 + "\n")


def _check_cli_available() -> str:
    """
    qwen-tts CLI 사용 가능 여부 확인

    Returns:
        qwen-tts CLI 경로

    Raises:
        TTSError: CLI가 설치되지 않은 경우
    """
    cli_path = shutil.which("qwen-tts")
    if not cli_path:
        logger.error("qwen-tts CLI가 설치되지 않았습니다.")
        logger.error("설치 방법: cargo install qwen_tts_cli --features metal,accelerate,audio-loading (macOS)")
        logger.error("           cargo install qwen_tts_cli --features cuda,flash-attn,cudnn,nccl,audio-loading (Linux)")
        raise TTSError("qwen-tts CLI가 설치되지 않았습니다. 'cargo install qwen_tts_cli'로 설치하세요.")
    return cli_path


def _get_device_arg() -> list:
    """
    시스템에 맞는 디바이스 인자 반환

    Returns:
        디바이스 인자 리스트 (예: ["--device", "metal"])
    """
    import platform

    system = platform.system()

    if system == "Darwin":
        # macOS - Metal 사용
        return ["--device", "metal"]
    elif system == "Linux":
        # Linux - CUDA 사용 가능하면 사용, 아니면 CPU
        # CUDA 확인은 CLI에 맡김 (기본값이 auto)
        return []
    else:
        # Windows 등 - 기본값 사용
        return []


def parse_yaml_to_text(yaml_path: str) -> str:
    """
    YAML 파일을 읽어 TTS 용 텍스트 스트립트로 변환

    Args:
        yaml_path: YAML 파일 경로

    Returns:
        TTS 변환용 텍스트
    """
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"YAML 파일을 찾을 수 없습니다: {yaml_path}")
        raise TTSError(f"YAML 파일을 찾을 수 없습니다: {yaml_path}")
    except yaml.YAMLError as e:
        logger.error(f"YAML 파싱 실패: {e}")
        raise TTSError(f"YAML 파싱 실패: {e}")
    except Exception as e:
        logger.error(f"YAML 로드 실패: {e}")
        raise TTSError(f"YAML 로드 실패: {e}")

    script = []

    # 메타데이터 처리
    meta = data.get("metadata", {})
    date = meta.get("date", "")
    time = meta.get("time", "")
    location = meta.get("location", "")

    # 날짜와 시간 포맷팅 (time 이 없으면 공백 제거)
    datetime_str = f"{date} {time} 기준입니다." if time else f"{date} 기준입니다."
    script.append(f"오늘의 베트남 주요 뉴스. {datetime_str}")
    if location:
        script.append(f"{location} 인근 정보를 포함합니다.")
    script.append("\n")

    # 섹션별 순회
    sections = data.get("sections", [])
    for section in sections:
        section_name = section.get("name", "")
        # 섹션 제목 (ex: 안전 및 기상 관제)
        script.append(f"{section_name}입니다.")

        items = section.get("items", [])
        if not items:
            script.append("현재 관련된 특이 사항이나 새로운 소식은 없습니다.")
            script.append("\n")
            continue

        for item in items:
            # 항목별 타이틀 (title 또는 name)
            title = item.get("title") or item.get("name")
            if title:
                script.append(f"{title}.")

            # 본문 내용
            content = item.get("content", "")
            if content:
                script.append(f"{content}")

            # 수치 정보 (날씨/공기 등)
            details = []
            if item.get("temp"): details.append(f"기온은 {item['temp']}입니다.")
            if item.get("humidity"): details.append(f"습도는 {item['humidity']}입니다.")
            if item.get("rain_chance"): details.append(f"강수 확률은 {item['rain_chance']}입니다.")
            if item.get("aqi"): details.append(f"AQI 지수는 {item['aqi']}입니다.")

            if details:
                script.append(" ".join(details))

            # 노트 (특이사항)
            note = item.get("note")
            if note:
                script.append(f"참고로 {note}")

            script.append("\n")

        script.append("\n") # 섹션 간 간격 (TTS 호흡 정리용)

    return "\n".join(script)


def _convert_wav_to_mp3(wav_path: str, mp3_path: str):
    """
    WAV 파일을 MP3로 변환

    Args:
        wav_path: 입력 WAV 파일 경로
        mp3_path: 출력 MP3 파일 경로
    """
    cmd = [
        'ffmpeg',
        '-y',
        '-i', wav_path,
        '-b:a', '128k',
        '-ar', '44100',
        mp3_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise TTSError(f"ffmpeg 변환 실패: {result.stderr}")

    logger.info(f"MP3 변환 완료: {mp3_path}")


async def generate_tts(
    text: str,
    output_path: str,
    voice: str = "sohee",
    language: str = "korean",
    instruct: str = None,
    model_name: str = None,
    device: str = "auto"
):
    """
    텍스트를 음성 파일로 변환 (qwen3-tts-rs CLI 래퍼)

    Args:
        text: 변환할 텍스트
        output_path: 출력 MP3 파일 경로
        voice: 화자 이름 (Sohee, Vivian, Serena 등)
        language: 언어 (Korean, English, Chinese, Japanese 등)
        instruct: 음성 스타일 설명 (VoiceDesign 모드)
        model_name: 모델 이름 (사용되지 않음, CLI 기본값 사용)
        device: 디바이스 설정 ("auto", "cuda", "metal", "cpu")

    Returns:
        생성된 MP3 파일 경로
    """
    # CLI 사용 가능 여부 확인
    cli_path = _check_cli_available()

    logger.info(f"Qwen3-TTS CLI 생성 시작 (Voice: {voice}, Language: {language})...")
    if instruct:
        logger.info(f"VoiceDesign 모드: {instruct}")

    # 언어 코드 변환 (Korean -> korean)
    lang_code = language.lower()

    # 임시 WAV 파일 경로
    temp_wav = output_path.replace(".mp3", ".tmp.wav")

    # CLI 인자 구성 (최상위 옵션 방식)
    cmd = [cli_path, "--text", text, "--output", temp_wav, "--language", lang_code]

    # 디바이스 설정
    if device != "auto":
        cmd.extend(["--device", device])
    else:
        cmd.extend(_get_device_arg())

    # 모드 선택
    if instruct:
        # VoiceDesign 모드: 자연어로 음성 설명
        cmd.extend(["--voice-design", instruct])
    else:
        # CustomVoice 모드: 미리 정의된 스피커 사용
        cmd.extend(["--speaker", voice.lower()])

    logger.info(f"CLI 실행: {' '.join(cmd)}")

    try:
        # CLI 실행 (실시간 로그 출력)
        result = subprocess.run(cmd, text=True)

        if result.returncode != 0:
            raise TTSError(f"qwen-tts CLI 실행 실패 (exit code: {result.returncode})")

        # WAV → MP3 변환
        _convert_wav_to_mp3(temp_wav, output_path)

        # 임시 파일 정리
        if os.path.exists(temp_wav):
            os.remove(temp_wav)

        logger.info(f"음성 파일 생성 완료: {output_path}")
        return output_path

    except TTSError:
        raise
    except Exception as e:
        logger.error(f"TTS 변환 실패: {e}")
        # 임시 파일 정리
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
        raise TTSError(f"TTS 변환 실패: {e}")


async def yaml_to_tts(
    yaml_path: str,
    voice: str = "sohee",
    language: str = "korean",
    instruct: str = None,
    model_name: str = None,
    device: str = "auto"
):
    """
    YAML 파일을 읽어서 동일한 경로에 mp3 생성

    Args:
        yaml_path: YAML 파일 경로
        voice: 화자 이름 (기본값: Sohee)
        language: 언어 (기본값: Korean)
        instruct: 음성 스타일 설명 (선택사항)
        model_name: 모델 이름 (사용되지 않음, CLI 기본값 사용)
        device: 디바이스 설정 ("auto", "cuda", "metal", "cpu")
    """
    if not os.path.exists(yaml_path):
        logger.error(f"파일을 찾을 수 없습니다: {yaml_path}")
        raise TTSError(f"파일을 찾을 수 없습니다: {yaml_path}")

    logger.info(f"YAML 파일 읽기 및 정제 시작: {yaml_path}")

    # 텍스트 변환
    try:
        tts_text = parse_yaml_to_text(yaml_path)
    except TTSError:
        raise
    except Exception as e:
        logger.error(f"텍스트 파싱 중 예기치 못한 오류: {e}")
        raise TTSError(f"텍스트 파싱 중 예기치 못한 오류: {e}")

    if not tts_text:
        logger.error("TTS 변환할 텍스트가 없습니다.")
        raise TTSError("TTS 변환할 텍스트가 없습니다.")

    # 출력 경로 설정 (YYMMDD_HHMM.yaml -> YYMMDD_HHMM.mp3)
    output_path = yaml_path.replace(".yaml", ".mp3")

    logger.info(f"TTS 변환 시작 (Voice: {voice}, Language: {language})...")
    logger.info(f"--- 스크립트 미리보기 ---\n{tts_text[:200]}...\n-----------------------")

    try:
        await generate_tts(
            text=tts_text,
            output_path=output_path,
            voice=voice,
            language=language,
            instruct=instruct,
            model_name=model_name,
            device=device
        )
        logger.info(f"음성 파일 생성 완료: {output_path}")
    except TTSError:
        raise
    except Exception as e:
        logger.error(f"TTS 변환 실패: {e}")
        raise TTSError(f"TTS 변환 실패: {e}")


if __name__ == "__main__":
    # 임시 테스트 케이스
    import sys
    target_file = sys.argv[1] if len(sys.argv) > 1 else "data/sample.yaml"
    asyncio.run(yaml_to_tts(target_file))
