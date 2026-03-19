#!/usr/bin/env python3
"""
Qwen3-TTS 빠른 테스트 도구
CLI 에서 텍스트와 음성 스타일을 지정하여 즉시 TTS 를 생성하고 재생합니다.

사용법:
    python tests/unit/test_qwen_quick.py "텍스트" "음성 스타일 설명" --voice 음성명
"""

import asyncio
import argparse
import os
import sys
import tempfile
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from today_vn_news.tts import yaml_to_tts, TTSEngine
from today_vn_news.tts.qwen import AVAILABLE_VOICES, list_available_voices


def print_voices():
    """사용 가능한 음성 목록 출력"""
    print("\n🎤 Qwen3-TTS 사용 가능한 음성:")
    print("-" * 60)
    for category, voices in AVAILABLE_VOICES.items():
        print(f"\n  [{category.upper()}]")
        for voice_name, info in voices.items():
            print(f"    • {voice_name:<20} ({info['lang']}/{info['gender']})")
    print("-" * 60)
    print()


async def generate_and_play(text: str, instruct: str, voice: str, language: str, model_name: str, no_play: bool = False):
    """
    TTS 생성 및 재생
    
    Args:
        text: 변환할 텍스트
        instruct: 음성 스타일 설명
        voice: 음성 이름
        language: 언어
        model_name: 모델 이름
        no_play: 재생 안함
    """
    print(f"\n🎤 TTS 생성 시작...")
    print(f"   텍스트: {text}")
    print(f"   음성: {voice}")
    print(f"   언어: {language}")
    print(f"   스타일: {instruct}")
    print(f"   모델: {model_name}")
    print()
    
    # 임시 YAML 생성
    yaml_content = f"""
metadata:
  date: "2026-03-19"
  time: "21:00"
  location: "Ho Chi Minh City"
sections:
  - name: "테스트"
    items:
      - title: "음성 테스트"
        content: "{text}"
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        f.write(yaml_content)
        temp_yaml = f.name
    
    try:
        # 출력 파일 경로
        temp_mp3 = temp_yaml.replace('.yaml', '.mp3')
        
        # TTS 생성
        print("⏳ TTS 생성 중... (첫 실행은 시간이 걸립니다)")
        await yaml_to_tts(
            yaml_path=temp_yaml,
            engine=TTSEngine.QWEN,
            voice=voice,
            language=language,
            instruct=instruct,
            model_name=model_name
        )
        
        print(f"\n✅ TTS 생성 완료!")
        print(f"   파일: {temp_mp3}")
        
        # 파일 크기 확인
        if os.path.exists(temp_mp3):
            size_kb = os.path.getsize(temp_mp3) / 1024
            print(f"   크기: {size_kb:.1f} KB")
        
        # 재생
        if not no_play:
            print("\n🔊 재생 중... (Ctrl+C 로 중지)")
            os.system(f"afplay '{temp_mp3}'")
        
        return temp_mp3
        
    finally:
        # 임시 파일 정리 (선택사항)
        # os.remove(temp_yaml)
        # if os.path.exists(temp_mp3):
        #     os.remove(temp_mp3)
        pass


async def main():
    parser = argparse.ArgumentParser(
        description="Qwen3-TTS 빠른 테스트 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 기본 테스트 (Sohee 음성)
  python test_qwen_quick.py "안녕하세요! 반가워요~" "밝은 정중한 아나운서 목소리"
  
  # 다른 음성 사용
  python test_qwen_quick.py "Hello! Nice to meet you." "Cheerful tone" --voice Aiden --language English
  
  # 일본어 테스트
  python test_qwen_quick.py "こんにちは！" "明るい女性の声" --voice Ono_Anna --language Japanese
  
  # 중국어 테스트
  python test_qwen_quick.py "你好！" "温柔的女声" --voice Vivian --language Chinese
  
  # 음성 목록 확인
  python test_qwen_quick.py --list-voices
  
  # 재생 없이 파일만 생성
  python test_qwen_quick.py "테스트" "스타일" --no-play
        """
    )
    
    parser.add_argument("text", nargs="?", help="변환할 텍스트")
    parser.add_argument("instruct", nargs="?", default="자연스러운 낭독", help="음성 스타일 설명")
    parser.add_argument("--voice", "-v", default="Sohee", 
                       help="음성 이름 (기본값: Sohee)")
    parser.add_argument("--language", "-l", default="Korean",
                       help="언어 (기본값: Korean)")
    parser.add_argument("--model", "-m", default="Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
                       help="모델 이름 (기본값: 0.6B)")
    parser.add_argument("--list-voices", action="store_true",
                       help="사용 가능한 음성 목록 출력")
    parser.add_argument("--no-play", action="store_true",
                       help="재생 없이 파일만 생성")
    parser.add_argument("--output", "-o", help="출력 파일 경로 (기본값: 임시파일)")
    
    args = parser.parse_args()
    
    # 음성 목록 확인
    if args.list_voices:
        list_available_voices()
        return
    
    # 인자 확인
    if not args.text:
        parser.print_help()
        print("\n❌ 오류: 텍스트를 입력해주세요.")
        print("예: python test_qwen_quick.py \"안녕하세요\" \"밝은 목소리\"")
        sys.exit(1)
    
    # 음성 검증
    voice_found = False
    for category, voices in AVAILABLE_VOICES.items():
        if args.voice in voices:
            voice_found = True
            break
    
    if not voice_found:
        print(f"\n⚠️  경고: '{args.voice}' 음성을 찾을 수 없습니다.")
        print_voices()
        print(f"기본 음성 'Sohee' 를 사용합니다.\n")
        args.voice = "Sohee"
    
    # TTS 생성 및 재생
    output_file = await generate_and_play(
        text=args.text,
        instruct=args.instruct,
        voice=args.voice,
        language=args.language,
        model_name=args.model,
        no_play=args.no_play
    )
    
    if args.output:
        # 지정한 경로로 파일 복사
        import shutil
        temp_mp3 = output_file
        shutil.copy(temp_mp3, args.output)
        print(f"\n💾 파일 저장: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
