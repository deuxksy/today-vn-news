# Aperture AI Gateway 통합 설계서

## 개요

번역 단계의 LLM 백엔드를 Google AI Studio에서 Tailscale Aperture AI Gateway로 변경한다.

## 배경

- 기존: Google AI Studio의 Gemma 3 27B 직접 호출
- 목표: Aperture를 통한 중앙 집중화된 AI Gateway 사용

## 변경 사항

### 1. 연결 정보

| 항목 | 기존 | 변경 |
|------|------|------|
| 엔드포인트 | Google AI Studio API | `https://ai.bun-bull.ts.net` |
| 인증 | API 키 (`GEMINI_API_KEY`) | Tailscale 인증 (키 없음) |
| 모델 | `gemma-3-27b-it` | `gemma-3-12b-it` |

### 2. 코드 변경 범위

**단일 파일**: `today_vn_news/translator.py`

### 3. 구현 상세

#### 3.1 환경변수

```bash
# Aperture 설정 (선택사항, 설정 시 Aperture 사용)
APERTURE_BASE_URL=https://ai.bun-bull.ts.net
APERTURE_MODEL=gemma-3-12b-it

# Fallback (Google AI Studio)
GEMINI_API_KEY=xxx
GEMINI_MODEL=gemma-3-27b-it
```

#### 3.2 클라이언트 및 모델 헬퍼 함수 (핵심 변경)

```python
def get_genai_client() -> tuple[genai.Client, str]:
    """
    Aperture 우선, Fallback으로 Google AI Studio 사용

    Returns:
        (Client, model_name) 튜플
    """
    base_url = os.getenv("APERTURE_BASE_URL")

    if base_url:
        # Aperture 사용 (Tailscale 인증)
        client = genai.Client(
            api_key="ts",  # Tailscale 인증용 더미 키
            http_options={"api_endpoint": base_url}
        )
        model = os.getenv("APERTURE_MODEL", "gemma-3-12b-it")
        return client, model

    # Fallback: Google AI Studio
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise TranslationError("API key not configured")
    client = genai.Client(api_key=api_key)
    model = os.getenv("GEMINI_MODEL", "gemma-3-27b-it")
    return client, model
```

#### 3.3 `_call_gemma_api()` 수정

기존 모델명 하드코딩을 인자로 변경:

```python
@with_api_retry(max_attempts=2)
def _call_gemma_api(client, model_name: str, prompt: str):
    return client.models.generate_content(
        model=model_name, contents=prompt
    )
```

### 4. 호환성 고려사항

- **Fallback**: `APERTURE_BASE_URL` 미설정 시 기존 Google AI Studio 동작 유지
- **테스트**: 기존 단위 테스트 수정 필요 (mock 엔드포인트 + `http_options` 파라미터)

### 5. 영향받는 함수 (총 5곳)

| 함수 | 변경 내용 |
|------|-----------|
| `get_genai_client()` | **신규** - 클라이언트 및 모델명 반환 헬퍼 |
| `_call_gemma_api()` | 모델명 인자 추가 (`model_name: str`) |
| `translate_weather_condition()` | `get_genai_client()` 사용 |
| `translate_articles()` | `get_genai_client()` 사용 |
| `translate_all_sources_parallel()` | 세마포어 주석 업데이트 ("Gemma API" → "Aperture/Gemini") |

### 6. 테스트 수정 범위

- `tests/unit/test_translator.py`
- Mock이 `http_options` 파라미터 처리 필요
- Aperture 사용/미사용 각각에 대한 테스트 케이스 추가

## 성공 기준

1. Aperture를 통한 번역 요청 성공
2. 기존 기능 (YAML 파싱, 에러 처리) 정상 동작
3. Fallback 시 기존 Google AI Studio 정상 동작

## 리스크

- **모델 크기 축소**: 27B → 12B로 번역 품질 변화 가능
- **네트워크**: Tailscale 연결 필수 (오프라인 시 번역 불가)

## 마일스톤

1. `translator.py` 수정
2. 단위 테스트 수정
3. 통합 테스트 (실제 Aperture 호출)
4. 검증 및 배포
