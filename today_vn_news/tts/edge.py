#!/usr/bin/env python3
import asyncio
import edge_tts
import os
import re

import yaml

from today_vn_news.logger import logger
from today_vn_news.exceptions import TTSError

"""
TTS 변환 모듈 (edge-tts Wrapper)
- 목적: YAML 파일을 파싱하여 텍스트를 추출하고 MP3 음성 파일로 변환
- 상세 사양: ContextFile.md 3.2 (기술 스택) 및 4장 (TTS 최적화 등) 참조
"""

async def generate_tts(text: str, output_path: str, voice: str = "ko-KR-SunHiNeural"):
    """
    텍스트를 음성 파일로 변환
    """
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def parse_yaml_to_text(yaml_path: str) -> str:
    """
    YAML 파일을 읽어 TTS용 텍스트 스트립트로 변환
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

    # 날짜와 시간 포맷팅 (time이 없으면 공백 제거)
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
            # temp, humidity, rain_chance, aqi, pm25 등
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

async def yaml_to_tts(yaml_path: str, voice: str = "ko-KR-SunHiNeural"):
    """
    YAML 파일을 읽어서 동일한 경로에 mp3 생성
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

    logger.info(f"TTS 변환 시작 (Voice: {voice})...")
    # print(f"--- 스크립트 미리보기 ---\n{tts_text[:200]}...\n-----------------------")

    try:
        await generate_tts(tts_text, output_path, voice)
        logger.info(f"음성 파일 생성 완료: {output_path}")
    except Exception as e:
        logger.error(f"TTS 변환 실패: {e}")
        raise TTSError(f"TTS 변환 실패: {e}")

if __name__ == "__main__":
    # 임시 테스트 케이스
    import sys
    target_file = sys.argv[1] if len(sys.argv) > 1 else "data/sample.yaml"
    asyncio.run(yaml_to_tts(target_file))
