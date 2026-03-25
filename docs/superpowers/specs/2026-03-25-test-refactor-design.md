# 테스트 코드 리팩토링 설계 문서

**날짜**: 2026-03-25
**목표**: 안정성 강화 + 가독성 개선
**범위**: 전체 테스트 코드 (18개 파일)

---

## 1. 개요

### 1.1 현재 문제

- **중복 코드**: scraper/translator/tts 테스트에 동일한 구조 반복
- **거대한 conftest.py**: 232줄, autouse fixture 복잡
- **파일 구조**: tests/unit/ 서브디렉토리가 불필요
- **불용 스크립트**: scripts/test_pushover_real.py (미사용)

### 1.2 리팩토링 목표

1. **안정성**: Fixture로 Mock/데이터 설정 중앙화, 테스트 간 독립성 보장
2. **가독성**: 테스트 코드의 의도와 행동이 명확하게 드러나도록
3. **최소주의**: 중복 제거만, 코드 자체로 의도 전달
4. **Flat 구조**: tests/ 바로 아래 파일 배치
5. **세분화**: 한 클래스에 2-3개 테스트만 (명확한 책임)

---

## 2. 아키텍처

### 2.1 최종 파일 구조

```
tests/
├── conftest.py                  # Fixtures + 기반 클래스 (간소화)
├── test_scraper.py              # 스크래퍼 (기반 클래스 활용)
├── test_translator.py           # 번역
├── test_tts.py                  # TTS
├── test_engine.py               # 영상 합성
├── test_timestamp.py            # 타임스탬프 유틸리티
├── test_exceptions.py           # 예외 처리
├── test_video_config.py         # 비디오 설정
├── test_media_archiver.py       # 미디어 아카이버
├── test_uploader.py             # 업로더
├── test_pushover.py             # Pushover
├── test_pipeline_status.py      # 파이프라인 상태
├── test_qwen_voices.py          # Qwen 음성
├── test_tts_qwen.py             # Qwen TTS
├── test_qwen_quick.py           # Qwen 빠른 테스트
└── integration/                 # 통합 테스트 유지
    └── test_done_file_verification.py
```

### 2.2 삭제 대상

- `tests/unit/` 디렉토리 (flat 구조로 통합)
- `tests/unit/test_notifications/` (test_pushover.py, test_pipeline_status.py로 승격)
- `tests/integration/test_pushover_integration.py` (중복)
- `scripts/test_pushover_real.py` (미사용)

---

## 3. 기반 클래스 설계

### 3.1 conftest.py 기반 클래스

```python
class BaseScraperTest:
    """
    스크래퍼 공통 테스트 기반 클래스 (직접 실행 금지)

    자식 클래스 속성:
        scraper_func: 스크래핑 함수
        source_name: 소스명
    """
    __test__ = False  # pytest가 이 클래스를 테스트로 수집하지 않음
    scraper_func = None
    source_name = None

    @pytest.mark.slow
    def test_real_api(self):
        """실제 API 호출 테스트"""
        if self.scraper_func is None:
            pytest.skip("scraper_func not defined")

        articles = self.scraper_func(TODAY)
        assert isinstance(articles, list)
        for article in articles:
            assert "title" in article
            assert "content" in article
            assert "url" in article


class BaseTranslatorTest:
    """
    번역 공통 테스트

    자식 클래스 속성:
        translator_func: 번역 함수
        mock_response_text: Mock 응답 데이터
    """
    translator_func = None
    mock_response_text = None

    @patch('today_vn_news.translator.get_genai_client')
    def test_translate_mock(self, mock_get_client):
        """Mock API로 번역 테스트"""
        if self.translator_func is None or self.mock_response_text is None:
            pytest.skip("translator_func or mock_response_text not defined")

        mock_response = Mock()
        mock_response.text = self.mock_response_text
        mock_client = AsyncMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = (mock_client, "test-model")

        result = self.translator_func([{"title": "Test", "content": "Test", "url": "https://example.com"}])
        assert result is not None
```

### 3.2 test_scraper.py 적용 예시

```python
from tests.conftest import BaseScraperTest

class TestScraperNhanDan(BaseScraperTest):
    scraper_func = scrape_nhandan
    source_name = "Nhân Dân"

class TestScraperTuoiTre(BaseScraperTest):
    scraper_func = scrape_tuoitre
    source_name = "Tuổi Trẻ"

class TestScraperVietnamNet(BaseScraperTest):
    scraper_func = scrape_vietnamnet
    source_name = "VietnamNet"
```

### 3.3 헬퍼 함수

```python
def assert_valid_articles(articles):
    """기사 리스트 구조 검증"""
    assert isinstance(articles, list)
    for article in articles:
        assert "title" in article
        assert "content" in article
        assert "url" in article
```

---

## 4. conftest.py 간소화

### 4.1 제거 대상

1. **autouse fixture** (`auto_save_scraped_yaml`)
2. **복잡한 fixture** (`save_scraped_yaml`)
3. **불용 Mock fixture** (`mock_http_response` 등 미사용)

### 4.2 유지 Fixtures

- 데이터 샘플 (`sample_weather_data`, `sample_sections`)
- 파일 관리 (`test_data_dir`, `sample_audio`, `yaml_file`)
- Mock fixture (필요한 것만)

---

## 5. 이전 순서

### 5.1 1단계: 기반 클래스 추가

- conftest.py에 `BaseScraperTest`, `BaseTranslatorTest` 추가
- 기존 테스트와 병존

### 5.2 2단계: 테스트 파일 변환

- test_scraper.py → 기반 클래스 상속 방식
- test_translator.py → 기반 클래스 상속 방식
- TDD 원칙: 테스트 통합 확인 후 커밋

### 5.3 3단계: 파일 구조 재편

- tests/unit/ → tests/ (flat 구조)
- tests/unit/test_notifications/* → tests/* (승격)
- tests/integration/test_pushover_integration.py 제거 (중복)

**검증**:
- 파일 이동 후 `pytest --collect-only`로 모든 테스트가 올바르게 수집되는지 확인
- import 경로 업데이트 필요 여부 검토

### 5.4 4단계: conftest.py 간소화

- autouse fixture 제거
- 불필요한 fixture 정리

### 5.5 5단계: scripts/ 삭제

- test_pushover_real.py 삭제

---

## 6. 검증 전략

### 6.1 테스트 실행

```bash
pytest tests/ -v
```

### 6.2 커버리지 확인

```bash
pytest --cov=today_vn_news --cov-report=html
```

### 6.3 속도 측정

```bash
pytest tests/ --durations=10
```

---

## 7. Rollback 계획

### 7.1 Git 전략

각 단계마다 커밋:
```bash
git commit -m "refactor(test): BaseScraperTest 추가"
```

### 7.2 복구 명령

```bash
# 마지막 커밋 취소 (작업 내용 보존)
git reset --soft HEAD~1

# 또는 커밋만 취소하고 변경사항 유지
git reset --mixed HEAD~1

# 파일 이동한 경우 복구 전략
git reflog  # 이동 전 커밋 확인
git reset --hard <이동-전-커밋-해시>
```

---

## 8. 성공 기준

1. ✅ 모든 테스트 통과
2. ✅ 커버리지 유지 또는 개선
3. ✅ conftest.py 줄 수 감소 (232줄 → 150줄 이하)
4. ✅ 테스트 실행 속도 유지 또는 개선
5. ✅ Flat 구조 달성
6. ✅ 중복 코드 제거

---

## 부록: 기반 클래스 패턴 장단점

### 장점

- 클래스 구조 유지 (세분화)
- 실제 코드는 기반 클래스에 한 번만 작성
- 속성 주입으로 간단한 설정

### 단점

- 상속으로 인한 복잡도 증가
- 테스트 실패 시 추적이 약간 어려울 수 있음
- 파이썬 매직 안티패턴 우려

### 왜 기반 클래스 선택했는가

1. 세분화 원칙 준수 (한 클래스에 2-3개 테스트)
2. test_scraper.py 이미 이 패턴으로 구조화됨
3. 11개 스크래퍼 클래스가 한 파일에 있어 유지보수 용이
