# 전체 시스템 점검 및 최적화 설계 문서

**작성일**: 2026-02-27
**프로젝트**: today-vn-news
**목표**: 안정성, 성능, 코드 품질 종합 개선

---

## 1. 개요

베트남 뉴스 자동화 파이프라인의 전체 시스템을 점검하고 안정성, 성능, 코드 품질 세 가지 측면에서 점진적으로 개선한다.

### 개선 범위

- **안정성 (Stability)**: 예외 처리 강화, 로깅 시스템 도입, 재시도 메커니즘
- **성능 (Performance)**: 번역 작업 병렬화
- **코드 품질 (Code Quality)**: 테스트 커버리지 확대, 문서화 표준화

---

## 2. 아키텍처

### 2.1 파일 구조 변경

```
today_vn_news/
├── __init__.py
├── logger.py          # 신규: 중앙 로거 설정
├── exceptions.py      # 신규: 커스텀 예외 클래스
├── retry.py           # 신규: 재시도 데코레이터
├── scraper.py         # 수정: 로깅, 예외 처리, 재시도 적용
├── translator.py      # 수정: 로깅, 예외 처리, 재시도, 병렬화 적용
├── tts.py             # 수정: 로깅, 예외 처리 적용
├── engine.py          # 수정: 로깅, 예외 처리 적용
└── uploader.py        # 수정: 로깅, 예외 처리, 재시도 적용

tests/
├── conftest.py        # 수정: Mock fixtures 추가
├── unit/              # 단위 테스트 (Mock 활용)
├── integration/       # 통합 테스트 (실제 API)
└── e2e/               # 신규: E2E 테스트
```

---

## 3. 상세 설계

### 3.1 단계 1: 로깅 시스템 도입 및 예외 처리 강화

#### 3.1.1 로깅 구조

```python
# today_vn_news/logger.py
import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logger(name: str = "today_vn_news") -> logging.Logger:
    """구조화된 로거 설정"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 포맷터
    formatter = logging.Formatter(
        "[{levelname}] {asctime} {name}:{funcName} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 콘솔 핸들러 (INFO 이상, 색상 지원)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 (DEBUG 이상, 일별 로테이션)
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(
        log_dir / f"today-vn-news-{datetime.now():%Y%m%d}.log",
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
```

#### 3.1.2 커스텀 예외 클래스

```python
# today_vn_news/exceptions.py
class TodayVnNewsError(Exception):
    """베이스 예외 클래스"""
    pass

class ScrapingError(TodayVnNewsError):
    """스크래핑 실패"""
    pass

class TranslationError(TodayVnNewsError):
    """번역 실패"""
    pass

class TTSError(TodayVnNewsError):
    """TTS 변환 실패"""
    pass

class VideoSynthesisError(TodayVnNewsError):
    """영상 합성 실패"""
    pass

class UploadError(TodayVnNewsError):
    """유튜브 업로드 실패"""
    pass
```

---

### 3.2 단계 2: API 재시도 메커니즘 추가

#### 3.2.1 재시도 전략

| API 유형 | 최대 재시도 | 초기 대기 | 최대 대기 | 재시도 조건 |
|---------|-----------|---------|---------|-----------|
| 스크래핑 (HTTP) | 3회 | 1초 | 10초 | 타임아웃, 5xx 에러 |
| Gemma 번역 | 2회 | 2초 | 15초 | 타임아웃, 429/5xx 에러 |
| YouTube 업로드 | 2회 | 3초 | 30초 | 네트워크 오류, 5xx |
| edge-tts | 1회 | 1초 | 5초 | 타임아웃만 |

#### 3.2.2 재시도 데코레이터

```python
# today_vn_news/retry.py
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import requests
import logging

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((requests.Timeout, requests.HTTPError)),
    before_sleep=lambda retry_state: logger.warning(
        f"HTTP 재시도 {retry_state.attempt_number}/3"
    )
)
def retry_http_request(func):
    """HTTP 요청 재시도 래퍼"""
    return func()

@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=2, min=2, max=15),
    retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    before_sleep=lambda retry_state: logger.warning(
        f"Gemma API 재시도 {retry_state.attempt_number}/2"
    )
)
def retry_gemma_api(func):
    """Gemma API 재시도 래퍼"""
    return func()
```

---

### 3.3 단계 3: 번역 작업 병렬화

#### 3.3.1 성능 개선 효과

| 항목 | 순차 처리 | 병렬 처리 | 개선폭 |
|-----|---------|---------|-------|
| 소요 시간 | 약 6~7분 | 약 2~3분 | ~60% 단축 |
| 동시 요청 | 1개 | 최대 3개 | - |
| API 요금 | 기준 | 기준 (동시 수 제한으로) | 동일 |

#### 3.3.2 비동기 번역 구조

```python
# today_vn_news/translator.py
import asyncio
from typing import List, Dict, Optional

async def translate_articles_async(
    articles: List[Dict[str, str]],
    source_name: str,
    today_str: str,
    max_articles: int = 2,
    semaphore: asyncio.Semaphore = None,
) -> Optional[List[Dict[str, str]]]:
    """비동기 번역 작업 (세마포어로 동시성 제어)"""
    if semaphore is None:
        semaphore = asyncio.Semaphore(3)

    async with semaphore:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            translate_articles,  # 기존 동기 함수
            articles, source_name, today_str, max_articles
        )

async def translate_all_sources_parallel(
    scraped_data: Dict,
    date_str: str,
) -> List[Dict]:
    """모든 뉴스 소스를 병렬로 번역"""
    source_order = [
        "안전 및 기상 관제", "Sức khỏe & Đời sống", "Nhân Dân",
        "Tuổi Trẻ", "VietnamNet", "VnExpress", "Thanh Niên",
        "The Saigon Times", "VietnamNet 정보통신", "VnExpress IT/과학",
    ]

    tasks = []
    for source_name in source_order:
        if source_name not in scraped_data or not scraped_data[source_name]:
            continue
        tasks.append(translate_articles_async(
            scraped_data[source_name], source_name, date_str,
            len(scraped_data[source_name])
        ))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    # 결과 처리 로직...
    return translated_sections
```

---

### 3.4 단계 4: 테스트 커버리지 확대 및 문서화

#### 3.4.1 테스트 구조

```
tests/
├── conftest.py           # Mock fixtures 추가
├── unit/                 # 단위 테스트 (Mock 활용)
├── integration/          # 통합 테스트 (실제 API)
└── e2e/                  # E2E 테스트
    └── test_full_pipeline.py
```

#### 3.4.2 Mock Fixtures

```python
# tests/conftest.py 추가
from unittest.mock import Mock, AsyncMock

@pytest.fixture
def mock_gemma_client():
    """Gemma API Mock"""
    client = AsyncMock()
    client.models.generate_content.return_value = Mock(
        text="""items:
  - title: 테스트 기사
    content: 테스트 내용입니다.
    url: https://example.com"""
    )
    return client
```

#### 3.4.3 커버리지 목표

| 모듈 | 목표 커버리지 |
|-----|--------------|
| scraper.py | 80% |
| translator.py | 85% |
| tts.py | 80% |
| engine.py | 75% |
| uploader.py | 70% |
| **전체** | **78%** |

---

## 4. 의존성 추가

```toml
# pyproject.toml
dependencies = [
    "tenacity>=9.0.0",  # 재시도 메커니즘
]
```

---

## 5. 구현 순서

1. 단계 1: 로깅 시스템 도입 및 예외 처리 강화 (2~3시간)
2. 단계 2: API 재시도 메커니즘 추가 (1~2시간)
3. 단계 3: 번역 작업 병렬화 (2~3시간)
4. 단계 4: 테스트 커버리지 확대 및 문서화 (3~4시간)

**총 예상 소요 시간**: 8~12시간

---

## 6. 검증 기준

- [ ] 로그가 `logs/today-vn-news-{date}.log`에 정상적으로 기록됨
- [ ] API 실패 시 재시도가 동작하고 로그에 기록됨
- [ ] 번역 작업이 병렬로 처리되어 전체 시간이 단축됨
- [ ] 테스트 커버리지가 78% 이상 달성함
- [ ] 모든 공개 함수에 docstring이 작성됨
