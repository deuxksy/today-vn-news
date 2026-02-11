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

TODAY = datetime.datetime.now().strftime("%Y-%m-%d")
NOW_TIME = datetime.datetime.now().strftime("%H:%M")


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
        "date": TODAY,
    }


@pytest.fixture
def sample_sections(sample_weather_data, sample_aqi_data, sample_news_article):
    """섹션 데이터 샘플"""
    return {
        "metadata": {
            "date": TODAY,
            "time": NOW_TIME,
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


@pytest.fixture(scope="session")
def test_data_dir():
    """테스트 데이터 디렉토리 (data/test)"""
    from pathlib import Path

    data_dir = Path("data/test")
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture
def yaml_file(sample_sections, test_data_dir, test_timestamp):
    """자동 생성되는 YAML 파일 (data/test에 저장)"""
    yaml_path = test_data_dir / f"{test_timestamp}.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(sample_sections, f)
    return yaml_path


@pytest.fixture
def save_scraped_yaml(test_data_dir):
    """
    스크래핑 테스트 후 YAML 자동 저장 Fixture

    사용법:
        def test_something(save_scraped_yaml):
            # 테스트 코드
            articles = scrape_xxx()
            # 테스트 끝나면 자동으로 YAML 저장됨
    """
    from today_vn_news.scraper import scrape_and_save

    saved_files = []

    def save_yaml():
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        raw_yaml_path = test_data_dir / f"{timestamp}_raw.yaml"

        # 오늘 날짜로 스크래핑 및 저장
        date_str = datetime.now().strftime("%Y-%m-%d")
        scrape_and_save(date_str, str(raw_yaml_path))
        saved_files.append(raw_yaml_path)

    yield save_yaml

    # finalizer: 테스트 후 YAML 저장
    # save_scraped_yaml fixture를 사용하는 테스트만 저장
    # (필요할 때 함수 호출로 저장)


@pytest.fixture(autouse=True)
def auto_save_scraped_yaml(test_data_dir, request):
    """
    스크래핑 단위 테스트가 실행될 때마다 YAML 자동 저장 (autouse)

    test_scraper.py의 테스트가 실행되면 자동으로 YAML을 data/test/에 저장합니다.
    """
    # test_scraper.py의 테스트만 대상
    module_name = request.module.__name__ if request.module else ""
    if "test_scraper" not in module_name:
        return

    # TestScraperFullSaveYaml는 이미 YAML을 저장하므로 스킵
    class_name = request.node.cls.__name__ if request.node.cls else ""
    if "TestScraperFullSaveYaml" in class_name:
        return

    from today_vn_news.scraper import scrape_and_save
    from datetime import datetime

    def save_after_test():
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            raw_yaml_path = test_data_dir / f"{timestamp}_raw.yaml"
            date_str = datetime.now().strftime("%Y-%m-%d")

            # 스크래핑 및 저장
            scrape_and_save(date_str, str(raw_yaml_path))
        except Exception as e:
            # 실패해도 테스트는 계속 진행
            pass

    # 테스트 종료 후 YAML 저장
    request.addfinalizer(save_after_test)
