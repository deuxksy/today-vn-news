# Aperture AI Gateway 통합 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 번역 백엔드를 Google AI Studio에서 Tailscale Aperture AI Gateway로 마이그레이션

**Architecture:** `get_genai_client()` 헬퍼 함수로 클라이언트 생성 및 모델명 선택을 중앙화. `APERTURE_BASE_URL` 환경변수 존재 여부로 Aperture/Fallback 자동 전환.

**Tech Stack:** Python 3.14, google-genai SDK, pytest

---

## 파일 구조

| 파일 | 변경 유형 | 설명 |
|------|-----------|------|
| `today_vn_news/translator.py` | Modify | 헬퍼 함수 추가, 기존 함수 수정 |
| `tests/unit/test_translator.py` | Modify | Aperture/Fallback 테스트 케이스 추가 |

---

### Task 1: `get_genai_client()` 헬퍼 함수 구현

**Files:**
- Modify: `today_vn_news/translator.py:19-36` (기존 `_call_gemma_api` 위에 추가)

- [ ] **Step 1: Aperture용 테스트 작성**

```python
# tests/unit/test_translator.py에 추가

@pytest.mark.unit
class TestGetGenaiClient:
    """get_genai_client 헬퍼 함수 테스트"""

    @patch.dict(os.environ, {"APERTURE_BASE_URL": "https://ai.test.ts.net", "APERTURE_MODEL": "test-model"})
    @patch('today_vn_news.translator.genai.Client')
    def test_get_genai_client_aperture(self, mock_client_class):
        """Aperture 설정 시 올바른 클라이언트와 모델 반환"""
        from today_vn_news.translator import get_genai_client

        client, model = get_genai_client()

        mock_client_class.assert_called_once_with(
            api_key="ts",
            http_options={"api_endpoint": "https://ai.test.ts.net"}
        )
        assert model == "test-model"

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": "gemini-model"}, clear=True)
    @patch('today_vn_news.translator.genai.Client')
    def test_get_genai_client_fallback(self, mock_client_class):
        """APERTURE_BASE_URL 없으면 Google AI Studio fallback"""
        from today_vn_news.translator import get_genai_client

        # APERTURE_BASE_URL 제거
        os.environ.pop("APERTURE_BASE_URL", None)

        client, model = get_genai_client()

        mock_client_class.assert_called_once_with(api_key="test-key")
        assert model == "gemini-model"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_genai_client_no_key_raises(self):
        """API 키 없으면 TranslationError 발생"""
        from today_vn_news.translator import get_genai_client

        os.environ.pop("APERTURE_BASE_URL", None)
        os.environ.pop("GEMINI_API_KEY", None)
        os.environ.pop("GOOGLE_API_KEY", None)

        with pytest.raises(TranslationError):
            get_genai_client()
```

- [ ] **Step 2: 테스트 실행 (실패 확인)**

Run: `uv run pytest tests/unit/test_translator.py::TestGetGenaiClient -v`
Expected: FAIL - `ImportError: cannot import name 'get_genai_client'`

- [ ] **Step 3: `get_genai_client()` 구현**

```python
# today_vn_news/translator.py 상단에 추가 (import 이후)

def get_genai_client() -> tuple[genai.Client, str]:
    """
    Aperture 우선, Fallback으로 Google AI Studio 사용

    Returns:
        (Client, model_name) 튜플

    Raises:
        TranslationError: API 키 미설정 시
    """
    base_url = os.getenv("APERTURE_BASE_URL")

    if base_url:
        # Aperture 사용 (Tailscale 인증)
        model = os.getenv("APERTURE_MODEL", "gemma-3-12b-it")
        client = genai.Client(
            api_key="ts",  # Tailscale 인증용 더미 키
            http_options={"api_endpoint": base_url}
        )
        return client, model

    # Fallback: Google AI Studio
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise TranslationError("API key not configured")

    model = os.getenv("GEMINI_MODEL", "gemma-3-27b-it")
    client = genai.Client(api_key=api_key)
    return client, model
```

- [ ] **Step 4: 테스트 실행 (통과 확인)**

Run: `uv run pytest tests/unit/test_translator.py::TestGetGenaiClient -v`
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add today_vn_news/translator.py tests/unit/test_translator.py
git commit -m "feat(translator): add get_genai_client helper with Aperture support"
```

---

### Task 2: `_call_gemma_api()` 수정

**Files:**
- Modify: `today_vn_news/translator.py:20-36`

- [ ] **Step 1: 테스트 수정**

기존 테스트에서 `model_name` 인자 추가하도록 mock 호출 방식 변경은 Task 3에서 일괄 처리. 여기서는 새로운 시그니처 테스트만 추가.

```python
# tests/unit/test_translator.py TestTranslationMock 클래스에 추가

    @patch('today_vn_news.translator.genai.Client')
    def test_call_gemma_api_with_model_name(self, mock_client_class):
        """_call_gemma_api가 model_name 인자를 올바르게 전달"""
        mock_response = MagicMock()
        mock_response.text = "test response"

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        from today_vn_news.translator import _call_gemma_api
        result = _call_gemma_api(mock_client, "custom-model", "test prompt")

        mock_client.models.generate_content.assert_called_once_with(
            model="custom-model",
            contents="test prompt"
        )
        assert result == mock_response
```

- [ ] **Step 2: 테스트 실행 (실패 확인)**

Run: `uv run pytest tests/unit/test_translator.py::TestTranslationMock::test_call_gemma_api_with_model_name -v`
Expected: FAIL - TypeError (wrong number of arguments)

- [ ] **Step 3: `_call_gemma_api()` 수정**

```python
# today_vn_news/translator.py - 기존 함수를 아래로 교체

@with_api_retry(max_attempts=2)
def _call_gemma_api(client, model_name: str, prompt: str):
    """
    Gemma API 호출 (재시도 적용)

    Args:
        client: GenAI 클라이언트
        model_name: 사용할 모델명
        prompt: 전송할 프롬프트

    Returns:
        API 응답 객체

    Raises:
        Exception: API 호출 실패 시 (최대 2회 재시도 후)
    """
    return client.models.generate_content(
        model=model_name, contents=prompt
    )
```

- [ ] **Step 4: 테스트 실행 (통과 확인)**

Run: `uv run pytest tests/unit/test_translator.py::TestTranslationMock::test_call_gemma_api_with_model_name -v`
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add today_vn_news/translator.py tests/unit/test_translator.py
git commit -m "refactor(translator): add model_name parameter to _call_gemma_api"
```

---

### Task 3: `translate_weather_condition()` 수정

**Files:**
- Modify: `today_vn_news/translator.py:39-87`

- [ ] **Step 1: 기존 테스트가 여전히 통과하는지 확인**

Run: `uv run pytest tests/unit/test_translator.py::TestWeatherTranslation -v`
Expected: PASS (사전 매칭 케이스만)

- [ ] **Step 2: 함수 수정**

```python
# today_vn_news/translator.py - translate_weather_condition 함수 교체

def translate_weather_condition(condition: str) -> str:
    """
    베트남어 기상 상태를 한국어로 번역

    Args:
        condition: 베트남어 기상 상태 (예: "Mây thay đổi, trời nắng")

    Returns:
        한국어 번역된 기상 상태
    """
    if not condition:
        return condition

    # 빠른 매칭 (사전 기반)
    weather_dict = {
        "mây thay đổi": "구름 낌",
        "trời nắng": "맑음",
        "trời mưa": "비",
        "trời giông": "천둥번개",
        "nhiều mây": "흐림",
        "trời âm u": "흐림",
        "mưa rào": "소나기",
        "sương mù": "안개",
        "mây tản": "흐림 → 맑음",
        "nóng": "더움",
        "lạnh": "추움",
        "trời đẹp": "좋음",
        "nắng đẹp": "맑고 좋음",
    }

    # 부분 매칭으로 복합 상태 처리
    translated = condition.lower()
    for vn, kr in weather_dict.items():
        translated = translated.replace(vn.lower(), kr)

    # 매칭 안되면 API 사용
    if translated == condition.lower():
        try:
            client, model_name = get_genai_client()
            prompt = f"베트남어 기상 상태 '{condition}'를 한국어 3글자 이내로 짧게 번역해주세요. 답변만 출력하세요."
            response = _call_gemma_api(client, model_name, prompt)
            if response.text:
                return response.text.strip()
        except Exception:
            pass

    return translated
```

- [ ] **Step 3: 테스트 실행**

Run: `uv run pytest tests/unit/test_translator.py::TestWeatherTranslation -v`
Expected: PASS

- [ ] **Step 4: 커밋**

```bash
git add today_vn_news/translator.py
git commit -m "refactor(translator): use get_genai_client in translate_weather_condition"
```

---

### Task 4: `translate_articles()` 수정

**Files:**
- Modify: `today_vn_news/translator.py:90-256`

- [ ] **Step 1: 기존 Mock 테스트 수정**

```python
# tests/unit/test_translator.py - TestTranslationMock 클래스의 기존 테스트 수정

    @patch('today_vn_news.translator.get_genai_client')
    def test_translate_articles_mock_api(self, mock_get_client):
        """Gemma API Mock을 활용한 번역 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.text = """items:
  - title: 테스트 기사 제목
    content: 테스트 기사 내용 요약입니다. 두 번째 줄입니다. 세 번째 줄입니다.
    url: https://example.com"""

        # Mock 클라이언트 설정
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        # get_genai_client가 (client, model_name) 튜플 반환
        mock_get_client.return_value = (mock_client, "test-model")

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
        assert result[0]["url"] == "https://example.com"

    @patch('today_vn_news.translator.get_genai_client')
    def test_translate_articles_mock_api_error(self, mock_get_client):
        """API 에러 발생 시 TranslationError 테스트"""
        # Mock 클라이언트 설정 - 예외 발생
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API Error")
        mock_get_client.return_value = (mock_client, "test-model")

        articles = [
            {
                "title": "Test Title",
                "content": "Test Content",
                "url": "https://example.com"
            }
        ]

        # TranslationError 발생 확인
        with pytest.raises(TranslationError):
            translate_articles(articles, "Test Source", "2026-02-27")

    @patch('today_vn_news.translator.get_genai_client')
    def test_translate_articles_mock_invalid_yaml(self, mock_get_client):
        """잘못된 YAML 응답 파싱 테스트"""
        # Mock 응답 설정 - 잘못된 YAML
        mock_response = MagicMock()
        mock_response.text = "invalid yaml content"

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = (mock_client, "test-model")

        articles = [
            {
                "title": "Test Title",
                "content": "Test Content",
                "url": "https://example.com"
            }
        ]

        # TranslationError 발생 확인
        with pytest.raises(TranslationError):
            translate_articles(articles, "Test Source", "2026-02-27")
```

- [ ] **Step 2: 테스트 실행 (실패 확인)**

Run: `uv run pytest tests/unit/test_translator.py::TestTranslationMock -v`
Expected: FAIL - mock 경로 변경으로 인한 실패

- [ ] **Step 3: `translate_articles()` 수정**

```python
# today_vn_news/translator.py - translate_articles 함수의 클라이언트 생성 부분만 수정
# 175-181행을 아래로 교체:

    # API 클라이언트 생성
    try:
        client, model_name = get_genai_client()
    except TranslationError:
        raise

    try:
        logger.info(f"{source_name} 기사 {len(articles_to_translate)}개 번역 시작")

        response = _call_gemma_api(client, model_name, prompt)
```

- [ ] **Step 4: 테스트 실행 (통과 확인)**

Run: `uv run pytest tests/unit/test_translator.py::TestTranslationMock -v`
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add today_vn_news/translator.py tests/unit/test_translator.py
git commit -m "refactor(translator): use get_genai_client in translate_articles"
```

---

### Task 5: 주석 정리 및 최종 검증

**Files:**
- Modify: `today_vn_news/translator.py:280, 343`

- [ ] **Step 1: 세마포어 주석 업데이트**

```python
# 280행 근처
semaphore = asyncio.Semaphore(3)  # AI Gateway 요금 제한 고려

# 343행 근처
semaphore = asyncio.Semaphore(3)  # AI Gateway 요금 제한 고려
```

- [ ] **Step 2: 전체 테스트 실행**

Run: `uv run pytest tests/unit/test_translator.py -v`
Expected: PASS

- [ ] **Step 3: 린터 실행**

Run: `uv run ruff check today_vn_news/translator.py`
Expected: No issues found

- [ ] **Step 4: 최종 커밋**

```bash
git add today_vn_news/translator.py
git commit -m "chore(translator): update semaphore comments for AI Gateway"
```

---

### Task 6: 통합 테스트 (수동)

- [ ] **Step 1: 환경변수 설정 확인**

```bash
# .env 파일에 추가
APERTURE_BASE_URL=https://ai.bun-bull.ts.net
APERTURE_MODEL=gemma-3-12b-it
```

- [ ] **Step 2: 실제 API 호출 테스트**

Run: `uv run pytest tests/unit/test_translator.py::TestTranslationRealAPI -v`
Expected: PASS (Tailscale 연결 필요)

- [ ] **Step 3: Release 커밋**

```bash
git add .
git commit -m "feat: integrate Tailscale Aperture AI Gateway for translation"
```

---

## 완료 기준

1. 모든 단위 테스트 통과
2. `APERTURE_BASE_URL` 설정 시 Aperture 사용
3. 미설정 시 기존 Google AI Studio 동작
4. Ruff 린트 통과
