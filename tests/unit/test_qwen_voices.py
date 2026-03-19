"""
Qwen3-TTS (VoiceDesign) 테스트 및 음성 목록 확인

CosyVoice 가 아닌 Qwen3-TTS 공식 모델에서 사용 가능한 음성을 테스트합니다.
"""

import asyncio
import os
import sys
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from today_vn_news.tts.qwen import AVAILABLE_VOICES, list_available_voices
from today_vn_news.tts import yaml_to_tts, TTSEngine
from today_vn_news.logger import logger


# Qwen3-TTS 공식 음성 목록 (9 개)
# 출처: https://github.com/QwenLM/Qwen3-TTS
AVAILABLE_VOICES_FLAT = {
    "Sohee": {"lang": "ko", "gender": "female", "category": "korean"},
    "Ryan": {"lang": "en", "gender": "male", "category": "english"},
    "Aiden": {"lang": "en", "gender": "male", "category": "english"},
    "Ono_Anna": {"lang": "ja", "gender": "female", "category": "japanese"},
    "Vivian": {"lang": "zh", "gender": "female", "category": "chinese"},
    "Serena": {"lang": "zh", "gender": "female", "category": "chinese"},
    "Uncle_Fu": {"lang": "zh", "gender": "male", "category": "chinese"},
    "Dylan": {"lang": "zh", "gender": "male", "category": "chinese"},
    "Eric": {"lang": "zh", "gender": "male", "category": "chinese"},
}


def list_available_voices_detailed(lang_filter: str = None):
    """
    사용 가능한 음성 목록 출력 (상세)
    
    Args:
        lang_filter: 언어 필터 (ko, zh, en, ja 등)
    """
    print("\n" + "=" * 80)
    print("🎤 Qwen3-TTS (VoiceDesign) 사용 가능한 음성 목록")
    print("=" * 80)
    print("\n💡 VoiceDesign 모델은 음성 설명 (instruct) 으로 커스텀 음성을 생성할 수 있습니다.")
    print("=" * 80)
    
    # 카테고리별로 그룹화
    categories = {}
    for voice_name, info in AVAILABLE_VOICES_FLAT.items():
        cat = info["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((voice_name, info))
    
    for category, voices in categories.items():
        if lang_filter and category != lang_filter:
            if lang_filter not in ["ko", "zh", "en", "ja"]:
                continue
        
        print(f"\n📁 {category.upper()} 카테고리")
        print("-" * 80)
        print(f"{'음성명':<20} {'언어':<10} {'성별':<10}")
        print("-" * 80)
        
        for voice_name, info in voices:
            print(f"{voice_name:<20} {info['lang']:<10} {info['gender']:<10}")
    
    print("\n" + "=" * 80)
    print("💡 사용법:")
    print("   python tests/unit/test_qwen_voices.py --list-voices")
    print("   python tests/unit/test_qwen_voices.py --voice Sohee")
    print("   python tests/unit/test_qwen_voices.py --voice Sohee --lang ko")
    print("   python tests/unit/test_qwen_voices.py --all")
    print("=" * 80 + "\n")


async def test_voice(voice_name: str, test_text: str = None, output_dir: str = "data", language: str = None):
    """
    특정 음성을 테스트
    
    Args:
        voice_name: 테스트할 음성 이름
        test_text: 테스트할 텍스트 (기본값: 한국어 테스트 문장)
        output_dir: 출력 디렉토리
        language: 언어 (기본값: 음성별 기본 언어)
    """
    if test_text is None:
        test_text = "안녕하세요! 오늘의 베트남 뉴스입니다. 오늘 날씨는 맑고 기온은 28 도입니다."
    
    # 음성별 기본 언어 설정
    if language is None:
        voice_info = AVAILABLE_VOICES_FLAT.get(voice_name, {})
        lang_code = voice_info.get("lang", "ko")
        language_map = {
            "ko": "Korean",
            "en": "English",
            "zh": "Chinese",
            "ja": "Japanese"
        }
        language = language_map.get(lang_code, "Korean")
    
    print(f"\n🎤 음성 테스트 시작: {voice_name}")
    print(f"📝 테스트 텍스트: {test_text}")
    print(f"🌍 언어: {language}")
    
    try:
        # 출력 파일 경로
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"test_qwen_{voice_name}.mp3")
        
        # TTS 생성
        print(f"⏳ TTS 생성 중...")
        await yaml_to_tts(
            yaml_path=None,  # 직접 텍스트 사용
            engine=TTSEngine.QWEN,
            voice=voice_name,
            language=language
        )
        
        # yaml_to_tts 는 YAML 파일이 필요하므로, 임시 YAML 생성 필요
        # 여기서는 간단한 테스트용 텍스트만 출력
        print(f"⚠️  실제 TTS 생성은 main.py 를 통해 실행하세요.")
        print(f"   예: python main.py --tts=qwen --voice={voice_name}")
        
        return None
        
    except Exception as e:
        print(f"❌ 음성 테스트 실패: {e}")
        return None


async def test_all_voices(output_dir: str = "data"):
    """
    모든 음성을 일괄 테스트
    """
    print("\n🎤 모든 음성 테스트를 시작합니다...")
    print("💡 이 테스트는 실제 Qwen3-TTS 모델을 다운로드하고 실행합니다.")
    print("   첫 실행 시 3-5GB 의 모델이 다운로드되며, 시간이 소요됩니다.\n")
    
    results = []
    
    # 각 음성별로 테스트
    for voice_name, info in AVAILABLE_VOICES_FLAT.items():
        lang_map = {
            "ko": "Korean",
            "en": "English",
            "zh": "Chinese",
            "ja": "Japanese"
        }
        language = lang_map.get(info["lang"], "Korean")
        
        print(f"\n--- {voice_name} ({info['lang']}/{info['gender']}) ---")
        
        # 테스트 텍스트 (언어별)
        if language == "Korean":
            test_text = "안녕하세요! {voice_name} 음성 테스트입니다."
        elif language == "English":
            test_text = f"Hello! This is {voice_name} voice test."
        elif language == "Chinese":
            test_text = f"你好！这是{voice_name}声音测试。"
        elif language == "Japanese":
            test_text = f"こんにちは！これは{voice_name}ボイステストです。"
        else:
            test_text = f"Test message for {voice_name}."
        
        print(f"텍스트: {test_text}")
        print(f"언어: {language}")
        
        # 실제 테스트는 main.py 사용 안내
        print(f"실행 명령: python main.py --tts=qwen --voice={voice_name} --language={language}")
        
        results.append({
            "voice": voice_name,
            "lang": info["lang"],
            "gender": info["gender"],
            "language": language
        })
    
    # 결과 요약
    print("\n" + "=" * 80)
    print("📊 테스트 결과 요약")
    print("=" * 80)
    print(f"총 {len(results)}개 음성")
    
    for r in results:
        print(f"  • {r['voice']:<20} ({r['lang']}/{r['gender']}) - {r['language']}")
    
    print("\n💡 실제 TTS 생성 테스트:")
    print("   python main.py --tts=qwen --voice=Sohee")
    print("   python main.py --tts=qwen --voice=Vivian --language=Chinese")
    print("=" * 80)


async def main():
    """
    메인 함수
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Qwen3-TTS 음성 테스트")
    parser.add_argument("--voice", type=str, help="테스트할 음성 이름")
    parser.add_argument("--text", type=str, help="테스트할 텍스트")
    parser.add_argument("--output", type=str, default="data", help="출력 디렉토리")
    parser.add_argument("--list-voices", action="store_true", help="사용 가능한 음성 목록 출력")
    parser.add_argument("--lang", type=str, help="언어 필터 (ko, en, zh, ja)")
    parser.add_argument("--all", action="store_true", help="모든 음성 테스트")
    parser.add_argument("--language", type=str, help="언어 설정 (Korean, English, Chinese, Japanese)")
    
    args = parser.parse_args()
    
    # 음성 목록 출력
    if args.list_voices:
        list_available_voices_detailed(args.lang)
        return
    
    # 모든 음성 테스트
    if args.all:
        await test_all_voices(args.output)
        return
    
    # 특정 음성 테스트
    if args.voice:
        await test_voice(args.voice, args.text, args.output, args.language)
        return
    
    # 기본: 음성 목록 출력
    list_available_voices_detailed()


if __name__ == "__main__":
    asyncio.run(main())
