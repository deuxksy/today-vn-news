"""
공통 Fixture 정의
- 테스트 데이터 샘플
- 파일 관리 (자동 cleanup)
"""

import pytest
import datetime
import yaml
from pathlib import Path
from typing import Dict

# ====== 데이터 Fixtures ======


@pytest.fixture
def test_timestamp():
    """테스트용 타임스탬프 (YYYYMMDD_HHMM)"""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M")


@pytest.fixture
def sample_weather_data():
    """기상 데이터 샘플"""
    return {"temp": "29", "humidity": "68", "condition": "Nhiều mây, không mưa"}


@pytest.fixture
def sample_aqi_data():
    """공기질 데이터 샘플"""
    return {"aqi": "115", "status": "Unhealthy", "pm25": "N/A", "pm10": "N/A"}


@pytest.fixture
def sample_news_article():
    """뉴스 기사 샘플"""
    return {
        "title": "ChatGPT 광고 시작",
        "content": "OpenAI는 사용자 경험 개선을 위해 광고를 도입한다.",
        "url": "https://vnexpress.net/...",
        "date": "2026-02-10",
    }


@pytest.fixture
def sample_sections(sample_weather_data, sample_aqi_data, sample_news_article):
    """섹션 데이터 샘플"""
    return {
        "metadata": {
            "date": "2026-02-10",
            "time": "16:00",
            "location": "Ho Chi Minh City",
        },
        "sections": [
            {
                "id": "1",
                "name": "안전 및 기상 관제",
                "priority": "P0",
                "items": [
                    {
                        "title": "기상 (NCHMF)",
                        "content": f"흐림, 온도 {sample_weather_data['temp']}°C",
                    },
                    {
                        "title": "공기질 (IQAir)",
                        "content": f"AQI {sample_aqi_data['aqi']}",
                    },
                ],
            },
            {
                "id": "2",
                "name": "VnExpress IT/과학",
                "priority": "P2",
                "items": [sample_news_article],
            },
        ],
    }


# ====== 파일 관리 Fixtures ======


@pytest.fixture
def test_data_dir(tmp_path):
    """자동 cleanup되는 테스트 데이터 디렉토리"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def yaml_file(sample_sections, test_data_dir, test_timestamp):
    """자동 생성/삭제되는 YAML 파일"""
    yaml_path = test_data_dir / f"{test_timestamp}.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(sample_sections, f)
    return yaml_path
