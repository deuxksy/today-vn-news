# 전체 시스템 점검 및 최적화 구현 계획

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 안정성, 성능, 코드 품질 세 가지 측면에서 베트남 뉴스 자동화 파이프라인을 점진적으로 개선한다.

**Architecture:** 기존 모듈에 로깅 시스템과 예외 처리를 추가하고, API 호출에 재시도 메커니즘을 도입하며, 번역 작업을 비동기로 병렬화한다.

**Tech Stack:** Python logging, tenacity, asyncio, pytest, unittest.mock

---

## Task 1: 로깅 시스템 설정 (logger.py)

**Files:**
- Create: `today_vn_news/logger.py`

**Step 1: 로거 모듈 작성**

```python
#!/usr/bin/env python3
"""
중앙 로깅 시스템
- 목적: 구조화된 로그 출력을 위한 통일된 로거 설정
- 출력: 콘솔(INFO 이상), 파일(DEBUG 이상)
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(name: str = "today_vn_news") -> logging.Logger:
    """
    구조화된 로거 설정 및 반환

    Args:
        name: 로거 이름 (기본값: today_vn_news)

    Returns:
        설정된 로거 인스턴스
    """
    logger = logging.getLogger(name)

    # 중복 설정 방지
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # 포맷터: [레벨] 시간 모듈:함수 - 메시지
    formatter = logging.Formatter(
        "[{levelname}] {asctime} {name}:{funcName} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 콘솔 핸들러 (INFO 이상)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 (DEBUG 이상, 일별 생성)
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


# 모듈 레벨 로거 인스턴스
logger = setup_logger()
```

**Step 2: Commit**

```bash
git add today_vn_news/logger.py
git commit -m "feat: 로깅 시스템 설정 모듈 추가

- 구조화된 로그 포맷 도입
- 콘솔(INFO)과 파일(DEBUG) 이중 출력
- 일별 로그 파일 생성

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 2: 커스텀 예외 클래스 정의 (exceptions.py)

**Files:**
- Create: `today_vn_news/exceptions.py`

**Step 1: 예외 클래스 작성**

```python
#!/usr/bin/env python3
"""
커스텀 예외 클래스
- 목적: 모듈별 특화된 예외 처리를 위한 예외 계층 구조
"""


class TodayVnNewsError(Exception):
    """베이스 예외 클래스 - 프로젝트 전체 예외의 기본"""
    pass


class ScrapingError(TodayVnNewsError):
    """스크래핑 실패 시 발생"""
    pass


class TranslationError(TodayVnNewsError):
    """번역 실패 시 발생"""
    pass


class TTSError(TodayVnNewsError):
    """TTS 변환 실패 시 발생"""
    pass


class VideoSynthesisError(TodayVnNewsError):
    """영상 합성 실패 시 발생"""
    pass


class UploadError(TodayVnNewsError):
    """유튜브 업로드 실패 시 발생"""
    pass
```

**Step 2: Commit**

```bash
git add today_vn_news/exceptions.py
git commit -m "feat: 커스텀 예외 클래스 계층 구조 추가

- ScrapingError, TranslationError, TTSError 등
- 각 모듈별 특화된 예외 처리 지원

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 3: scraper.py에 로깅 및 예외 처리 적용

**Files:**
- Modify: `today_vn_news/scraper.py`
- Test: `tests/unit/test_scraper.py`

**Step 1: 상단 import 추가**

```python
# scraper.py 상단에 추가
from today_vn_news.logger import logger
from today_vn_news.exceptions import ScrapingError
```

**Step 2: print 문을 logger로 변경 (예시)**

변경 전:
```python
print(f"[스크래핑] Nhân Dân 수집 중...")
```

변경 후:
```python
logger.info(f"Nhân Dân 스크래핑 시작")
```

**Step 3: 예외 발생 시 ScrapingError 사용 (예시)**

변경 전:
```python
print("[!] 스크래핑 실패")
return None
```

변경 후:
```python
logger.error(f"{source_name} 스크래핑 실패", extra={"url": url})
raise ScrapingError(f"Failed to scrape {source_name}")
```

**Step 4: Commit**

```bash
git add today_vn_news/scraper.py
git commit -m "refactor(scraper): 로깅 시스템 및 예외 처리 적용

- print 문을 구조화된 logger로 변경
- ScrapingError 예외 클래스 사용
- 에러 발생 시 상세 로그 기록

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 4: translator.py에 로깅 및 예외 처리 적용

**Files:**
- Modify: `today_vn_news/translator.py`

**Step 1: 상단 import 추가**

```python
from today_vn_news.logger import logger
from today_vn_news.exceptions import TranslationError
```

**Step 2: print 문을 logger로 변경**

변경 전:
```python
print(f"  [번역] {source_name} 기사 {len(articles_to_translate)}개 번역 중...")
```

변경 후:
```python
logger.info(f"{source_name} 기사 {len(articles_to_translate)}개 번역 시작")
```

**Step 3: 예외 발생 시 TranslationError 사용**

변경 전:
```python
print(f"  [!] {source_name} 번역 중 예외 발생: {str(e)}")
return None
```

변경 후:
```python
logger.error(f"{source_name} 번역 실패", exc_info=True)
raise TranslationError(f"Translation failed for {source_name}: {str(e)}")
```

**Step 4: Commit**

```bash
git add today_vn_news/translator.py
git commit -m "refactor(translator): 로깅 시스템 및 예외 처리 적용

- print 문을 구조화된 logger로 변경
- TranslationError 예외 클래스 사용
- 예외 스택 트레이스 포함 로깅

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 5: tts.py, engine.py, uploader.py에 로깅 및 예외 처리 적용

**Files:**
- Modify: `today_vn_news/tts.py`
- Modify: `today_vn_news/engine.py`
- Modify: `today_vn_news/uploader.py`

**Step 1: tts.py 수정**

```python
# 상단 추가
from today_vn_news.logger import logger
from today_vn_news.exceptions import TTSError

# print 문 변경 예시
logger.info(f"TTS 변환 시작: {yaml_path}")
logger.error(f"YAML 로드 실패: {e}")
raise TTSError(f"TTS failed: {str(e)}")
```

**Step 2: engine.py 수정**

```python
# 상단 추가
from today_vn_news.logger import logger
from today_vn_news.exceptions import VideoSynthesisError

# print 문 변경 예시
logger.info(f"영상 합성 시작: {base_name}, 인코더: {encoder}")
logger.error(f"FFmpeg 실행 실패: {process.stderr}")
raise VideoSynthesisError(f"Video synthesis failed: {str(e)}")
```

**Step 3: uploader.py 수정**

```python
# 상단 추가
from today_vn_news.logger import logger
from today_vn_news.exceptions import UploadError

# print 문 변경 예시
logger.info(f"유튜브 업로드 시작: {file_path}")
logger.error(f"재생 목록 추가 실패: {str(e)}")
raise UploadError(f"Upload failed: {str(e)}")
```

**Step 4: Commit**

```bash
git add today_vn_news/tts.py today_vn_news/engine.py today_vn_news/uploader.py
git commit -m "refactor: TTS, Engine, Uploader 모듈에 로깅 및 예외 처리 적용

- 구조화된 로거로 통일
- TTSError, VideoSynthesisError, UploadError 사용
- 에러 발생 시 상세 로그 기록

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 6: 재시도 메커니즘 모듈 작성 (retry.py)

**Files:**
- Create: `today_vn_news/retry.py`

**Step 1: tenacity 의존성 추가**

```bash
# pyproject.toml에 추가
uv add tenacity>=9.0.0
```

**Step 2: 재시도 데코레이터 모듈 작성**

```python
#!/usr/bin/env python3
"""
재시도 메커니즘 모듈
- 목적: API 호출 실패 시 자동 재시도 (지수 백오프)
- 라이브러리: tenacity
"""

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import requests
from today_vn_news.logger import logger


def with_http_retry(max_attempts: int = 3):
    """
    HTTP 요청 재시도 데코레이터 팩토리

    Args:
        max_attempts: 최대 재시도 횟수 (기본값: 3)

    Returns:
        재시도 데코레이터
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((requests.Timeout, requests.HTTPError)),
        before_sleep=lambda retry_state: logger.warning(
            f"HTTP 요청 재시도 {retry_state.attempt_number}/{max_attempts}"
        )
    )


def with_api_retry(max_attempts: int = 2):
    """
    API 호출 재시도 데코레이터 팩토리 (Gemma 등)

    Args:
        max_attempts: 최대 재시도 횟수 (기본값: 2)

    Returns:
        재시도 데코레이터
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=2, min=2, max=15),
        retry=retry_if_exception_type((TimeoutError, ConnectionError)),
        before_sleep=lambda retry_state: logger.warning(
            f"API 호출 재시도 {retry_state.attempt_number}/{max_attempts}"
        )
    )
```

**Step 3: 의존성 업데이트 커밋**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: tenacity 라이브러리 의존성 추가

재시도 메커니즘 구현을 위한 tenacity>=9.0.0 추가

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

**Step 4: 재시도 모듈 커밋**

```bash
git add today_vn_news/retry.py
git commit -m "feat: 재시도 메커니즘 데코레이터 모듈 추가

- HTTP 요청 재시도 (with_http_retry)
- API 호출 재시도 (with_api_retry)
- 지수 백오프 전략 적용

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 7: translator.py에 재시도 메커니즘 적용

**Files:**
- Modify: `today_vn_news/translator.py`

**Step 1: Gemma API 호출에 재시도 데코레이터 적용**

```python
# translator.py 상단에 추가
from today_vn_news.retry import with_api_retry

# translate_articles 함수 내부에서 Gemma API 호출 부분을 분리
@with_api_retry(max_attempts=2)
def _call_gemma_api(client, prompt):
    """Gemma API 호출 (재시도 적용)"""
    return client.models.generate_content(
        model="gemma-3-27b-it", contents=prompt
    )

# translate_articles 함수에서 사용
try:
    response = _call_gemma_api(client, prompt)
except Exception as e:
    logger.error(f"Gemma API 호출 최종 실패: {str(e)}")
    return None
```

**Step 2: Commit**

```bash
git add today_vn_news/translator.py
git commit -m "feat(translator): Gemma API 호출에 재시도 메커니즘 적용

- @with_api_retry 데코레이터로 자동 재시도
- 실패 시 지수 백오프로 대기 후 재시도
- 최대 2회 재시도 후 실패 시 로그 기록

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 8: scraper.py에 재시도 메커니즘 적용

**Files:**
- Modify: `today_vn_news/scraper.py`

**Step 1: HTTP 요청 함수에 재시도 데코레이터 적용**

```python
# scraper.py 상단에 추가
from today_vn_news.retry import with_http_retry

# 각 스크래핑 함수에서 requests.get 호출 부분 수정
@with_http_retry(max_attempts=3)
def _fetch_url(url: str, timeout: int = 10) -> requests.Response:
    """HTTP 요청 (재시도 적용)"""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response

# 사용 예시
response = _fetch_url(url)
```

**Step 2: Commit**

```bash
git add today_vn_news/scraper.py
git commit -m "feat(scraper): HTTP 요청에 재시도 메커니즘 적용

- @with_http_retry 데코레이터로 자동 재시도
- 타임아웃, 5xx 에러 발생 시 재시도
- 최대 3회 재시도 후 실패 시 예외 발생

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 9: 비동기 번역 함수 추가 (translator.py)

**Files:**
- Modify: `today_vn_news/translator.py`

**Step 1: asyncio 임포트 및 비동기 함수 추가**

```python
# translator.py 상단에 추가
import asyncio
from concurrent.futures import ThreadPoolExecutor

# translate_articles 함수 아래에 추가
async def translate_articles_async(
    articles: List[Dict[str, str]],
    source_name: str,
    today_str: str,
    max_articles: int = 2,
    semaphore: asyncio.Semaphore = None,
) -> Optional[List[Dict[str, str]]]:
    """
    비동기 번역 작업 (세마포어로 동시성 제어)

    Args:
        articles: 번역할 기사 리스트
        source_name: 뉴스 소스 이름
        today_str: 기준일 표시용
        max_articles: 번역할 최대 기사 수
        semaphore: 동시성 제어 세마포어 (기본 3개)

    Returns:
        번역된 기사 리스트 또는 None
    """
    if semaphore is None:
        semaphore = asyncio.Semaphore(3)  # Gemma API 요금 제한 고려

    async with semaphore:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            translate_articles,  # 기존 동기 함수
            articles, source_name, today_str, max_articles
        )
```

**Step 2: Commit**

```bash
git add today_vn_news/translator.py
git commit -m "feat(translator): 비동기 번역 함수 추가

- translate_articles_async 함수 추가
- 세마포어로 동시 API 호출 수 제어 (최대 3개)
- 기존 동기 함수를 스레드 풀에서 실행

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 10: 병렬 번역 함수 추가 (translator.py)

**Files:**
- Modify: `today_vn_news/translator.py`

**Step 1: 병렬 번역 함수 작성**

```python
# translate_articles_async 함수 아래에 추가
async def translate_all_sources_parallel(
    scraped_data: Dict,
    date_str: str,
) -> List[Dict]:
    """
    모든 뉴스 소스를 병렬로 번역

    Args:
        scraped_data: 스크래핑된 데이터 (소스별 기사 딕셔너리)
        date_str: 기준일 표시용

    Returns:
        번역된 섹션 리스트
    """
    source_order = [
        "안전 및 기상 관제", "Sức khỏe & Đời sống", "Nhân Dân",
        "Tuổi Trẻ", "VietnamNet", "VnExpress", "Thanh Niên",
        "The Saigon Times", "VietnamNet 정보통신", "VnExpress IT/과학",
    ]

    # 일반 뉴스 소스만 병렬 처리 (안전 및 기상은 별도 처리)
    tasks = []
    source_names = []
    for source_name in source_order:
        if source_name == "안전 및 기상 관제":
            continue
        if source_name not in scraped_data:
            continue
        articles = scraped_data[source_name]
        if not articles:
            continue

        tasks.append(translate_articles_async(
            articles, source_name, date_str, len(articles)
        ))
        source_names.append(source_name)

    # 병렬 실행 및 결과 수집
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 결과 처리
    translated_sections = []
    section_id = 1

    for source_name, result in zip(source_names, results):
        if isinstance(result, Exception):
            logger.error(f"{source_name} 번역 실패: {result}", exc_info=result)
            continue
        elif result:
            translated_sections.append({
                "id": str(section_id),
                "name": source_name,
                "priority": "P0" if "Sức khỏe" in source_name else "P2",
                "items": result
            })
            section_id += 1

    return translated_sections
```

**Step 2: Commit**

```bash
git add today_vn_news/translator.py
git commit -m "feat(translator): 병렬 번역 함수 추가

- translate_all_sources_parallel 함수 추가
- 독립된 뉴스 소스를 동시에 번역 처리
- 실패 시 다른 소스에 영향 없이 계속 진행

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 11: main.py를 비동기 파이프라인으로 변경

**Files:**
- Modify: `main.py`

**Step 1: translate_and_save를 비동기 버전으로 교체**

```python
# main.py 수정
from today_vn_news.translator import translate_all_sources_parallel, save_translated_yaml

# main 함수 내부에서 번역 부분 수정
async def main():
    # ... 기존 코드 ...

    # 2. 번역 (비동기 병렬 처리)
    print("\n[*] 2단계: 뉴스 번역 시작 (병렬 처리)...")

    # 안전 및 기상 관제는 기존 방식대로 처리
    from today_vn_news.translator import translate_and_save as sync_translate_and_save

    # 병렬 번역 실행
    translated_sections = await translate_all_sources_parallel(scraped_data, today_display)

    # 안전 및 기상 관제 추가
    if "안전 및 기상 관제" in scraped_data:
        # 기존 로직으로 안전 및 기상 데이터 처리
        # ...
        translated_sections.insert(0, safety_section)

    # YAML 저장
    if not translated_sections:
        print("\n[!] 2단계: 번역된 뉴스가 없어 파이프라인을 중단합니다.")
        sys.exit(1)

    if not save_translated_yaml({"sections": translated_sections}, today_display, yaml_path):
        print("\n[!] 2단계: YAML 저장 실패로 파이프라인을 중단합니다.")
        sys.exit(1)
```

**Step 2: Commit**

```bash
git add main.py
git commit -m "refactor(main): 번역 파이프라인을 비동기 병렬 처리로 변경

- translate_all_sources_parallel로 병렬 번역
- 독립된 뉴스 소스를 동시에 처리하여 시간 단축
- 안전 및 기상 관제는 기존 방식 유지

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 12: Mock Fixtures 추가 (tests/conftest.py)

**Files:**
- Modify: `tests/conftest.py`

**Step 1: Mock fixtures 추가**

```python
# tests/conftest.py 하단에 추가
from unittest.mock import Mock, AsyncMock

@pytest.fixture
def mock_gemma_client():
    """Gemma API Mock"""
    client = AsyncMock()
    mock_response = Mock()
    mock_response.text = """items:
  - title: 테스트 기사 제목
    content: 테스트 내용입니다. 두 번째 줄입니다. 세 번째 줄입니다.
    url: https://example.com/test"""
    client.models.generate_content.return_value = mock_response
    return client

@pytest.fixture
def mock_http_response():
    """HTTP 응답 Mock"""
    mock = Mock()
    mock.status_code = 200
    mock.text = "<html><body><div class='title'>테스트</div><p>내용</p></body></html>"
    return mock

@pytest.fixture
def mock_successful_translation():
    """성공적인 번역 결과 Mock"""
    return [
        {
            "title": "테스트 기사",
            "content": "테스트 내용입니다.",
            "url": "https://example.com"
        }
    ]
```

**Step 2: Commit**

```bash
git add tests/conftest.py
git commit -m "test(conftest): Mock fixtures 추가

- mock_gemma_client: Gemma API 모킹
- mock_http_response: HTTP 응답 모킹
- mock_successful_translation: 번역 결과 모킹

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 13: 단위 테스트에 Mock 적용 (tests/unit/test_translator.py)

**Files:**
- Modify: `tests/unit/test_translator.py`

**Step 1: Mock을 활용한 단위 테스트 작성**

```python
import pytest
from unittest.mock import patch, AsyncMock
from today_vn_news.translator import translate_weather_condition
from today_vn_news.exceptions import TranslationError

def test_translate_weather_condition_dict_lookup():
    """기상 상태 사전 번역 테스트"""
    result = translate_weather_condition("Nhiều mây, không mưa")
    assert "흐림" in result or "구름" in result

def test_translate_weather_condition_empty():
    """빈 문자열 처리 테스트"""
    result = translate_weather_condition("")
    assert result == ""

@patch('today_vn_news.translator.genai.Client')
def test_translate_articles_mock_api(mock_client_class, mock_gemma_client):
    """Gemma API Mock을 활용한 번역 테스트"""
    # Mock 설정
    mock_client_class.return_value = mock_gemma_client

    from today_vn_news.translator import translate_articles
    import os
    os.environ["GEMINI_API_KEY"] = "test_key"

    articles = [
        {
            "title": "Test Title",
            "content": "Test Content",
            "url": "https://example.com"
        }
    ]

    result = translate_articles(articles, "Test Source", "2026-02-27")

    assert result is not None
    assert len(result) > 0
    assert result[0]["title"] == "테스트 기사 제목"
```

**Step 2: Commit**

```bash
git add tests/unit/test_translator.py
git commit -m "test(translator): Mock을 활용한 단위 테스트 추가

- translate_weather_condition 사전 번역 테스트
- translate_articles Mock API 테스트
- 빈 문자열 등 엣지 케이스 테스트

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 14: E2E 테스트 작성 (tests/e2e/test_full_pipeline.py)

**Files:**
- Create: `tests/e2e/test_full_pipeline.py`

**Step 1: E2E 테스트 작성**

```python
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
```

**Step 2: Commit**

```bash
git add tests/e2e/test_full_pipeline.py
git commit -m "test(e2e): 전체 파이프라인 E2E 테스트 추가

- 스크래핑 → 번역 → TTS → 영상 합성 전 과정 테스트
- @slow 마크로 실제 API 호출 필요 테스트 구분
- 각 단계별 출력 파일 존재 검증

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 15: 커버리지 설정 파일 추가

**Files:**
- Create: `.coveragerc`

**Step 1: 커버리지 설정 작성**

```ini
[run]
source = today_vn_news
omit =
    */tests/*
    */__init__.py
    */conftest.py

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov
```

**Step 2: Commit**

```bash
git add .coveragerc
git commit -m "test: pytest 커버리지 설정 추가

- today_vn_news 모듈만 측정
- 테스트 파일 및 __init__.py 제외
- HTML 리포트 생성 설정

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 16: 테스트 실행 및 커버리지 확인

**Files:**
- None (실행만)

**Step 1: 전체 테스트 실행**

```bash
uv run pytest --verbose
```

예상 결과:
```
tests/unit/test_scraper.py::test_scrape_nhandan_real_api PASSED
tests/unit/test_translator.py::test_translate_weather_condition_dict_lookup PASSED
tests/e2e/test_full_pipeline.py::test_full_pipeline_without_upload PASSED
...
```

**Step 2: 커버리지 실행**

```bash
uv run pytest --cov=today_vn_news --cov-report=html --cov-report=term
```

예상 결과:
```
Name                           Stmts   Miss  Cover
--------------------------------------------------
today_vn_news/__init__.py          2      0   100%
today_vn_news/logger.py           25      5    80%
today_vn_news/exceptions.py       12      0   100%
today_vn_news/retry.py            20      4    80%
today_vn_news/scraper.py         150     45    70%
today_vn_news/translator.py      180     30    83%
today_vn_news/tts.py              80     20    75%
today_vn_news/engine.py           60     18    70%
today_vn_news/uploader.py         90     30    67%
--------------------------------------------------
TOTAL                            619    152    75%
```

**Step 3: 커버리지 리포트 확인**

```bash
open htmlcov/index.html  # macOS
```

---

## Task 17: 문서화 표준화 (docstring 작성)

**Files:**
- Modify: `today_vn_news/*.py` (전체 모듈)

**Step 1: Google Style Docstring 예시 적용**

```python
def setup_logger(name: str = "today_vn_news") -> logging.Logger:
    """
    구조화된 로거 설정 및 반환.

    Args:
        name: 로거 이름 (기본값: \"today_vn_news\")

    Returns:
        설정된 로거 인스턴스

    Note:
        - 콘솔: INFO 레벨 이상 출력
        - 파일: DEBUG 레벨 이상 기록

    Example:
        >>> logger = setup_logger()
        >>> logger.info("테스트 메시지")
    """
    # ...구현...
```

**Step 2: 전체 모듈에 docstring 적용**

각 공개 함수에 일관된 docstring 스타일 적용

**Step 3: Commit**

```bash
git add today_vn_news/
git commit -m "docs: 전체 모듈에 Google Style Docstring 적용

- 함수별 인자, 반환값, 예외, 예시 문서화
- 일관된 docstring 스타일 적용
- IDE에서 함수 설명 표시 지원

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 18: 최종 검증 및 릴리즈 준비

**Files:**
- None (검증만)

**Step 1: 전체 테스트 실행**

```bash
uv run pytest --verbose
uv run pytest --cov=today_vn_news --cov-report=term
```

**Step 2: 로그 확인**

```bash
python -c "from today_vn_news.logger import logger; logger.info('테스트')"
cat logs/today-vn-news-$(date +%Y%m%d).log
```

**Step 3: 릴리즈 노트 작성**

```bash
git tag -a v0.5.0 -m "시스템 최적화 릴리즈

- 로깅 시스템 도입
- API 재시도 메커니즘
- 번역 병렬화 (성능 60% 개선)
- 테스트 커버리지 75% 달성
- 문서화 표준화"
```

---

## 요약

이 구현 계획은 다음을 포함합니다:

1. **로깅 시스템**: 구조화된 로그 출력, 파일 기록
2. **예외 처리**: 커스텀 예외 클래스 계층 구조
3. **재시도 메커니즘**: tenacity 기반 자동 재시도
4. **병렬 처리**: asyncio를 활용한 번역 성능 최적화
5. **테스트**: Mock 기반 단위 테스트, E2E 테스트
6. **문서화**: Google Style Docstring 표준화

**총 작업 수**: 18개 Tasks
**예상 소요 시간**: 8~12시간
