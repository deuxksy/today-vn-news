#!/usr/bin/env python3
"""
E2E (End-to-End) 테스트
- 목적: 전체 파이프라인이 정상 동작하는지 검증
"""

import pytest
import asyncio
import os
from pathlib import Path
from today_vn_news.scraper import scrape_and_save
from today_vn_news.translator import translate_and_save
from today_vn_news.tts import yaml_to_tts
from today_vn_news.engine import synthesize_video


@pytest.mark.slow
def test_full_pipeline_without_upload(test_timestamp):
    """
    전체 파이프라인 테스트 (유튜브 업로드 제외)

    1. 스크래핑
    2. 번역
    3. TTS
    4. 영상 합성
    """
    # 데이터 디렉토리
    data_dir = Path("data/test")
    data_dir.mkdir(parents=True, exist_ok=True)

    # 1. 스크래핑
    raw_yaml_path = data_dir / f"{test_timestamp}_raw.yaml"
    today_iso = "2026-02-27"

    scraped_data = scrape_and_save(today_iso, str(raw_yaml_path))
    assert scraped_data is not None
    assert raw_yaml_path.exists()

    # 2. 번역
    yaml_path = data_dir / f"{test_timestamp}.yaml"
    today_display = "2026년 2월 27일 12:00"

    result = translate_and_save(scraped_data, today_display, str(yaml_path))
    assert result is True
    assert yaml_path.exists()

    # 3. TTS (비동기)
    asyncio.run(yaml_to_tts(str(yaml_path)))
    mp3_path = data_dir / f"{test_timestamp}.mp3"
    assert mp3_path.exists()

    # 4. 영상 합성 (기본 이미지 존재 시)
    if Path("assets/default_bg.png").exists():
        result = synthesize_video(test_timestamp, str(data_dir))
        assert result is True
        final_video = data_dir / f"{test_timestamp}_final.mp4"
        assert final_video.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
