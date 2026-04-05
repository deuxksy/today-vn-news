# Gemma-4 번역 모델 업그레이드 설계서

> **상태**: Completed
> **날짜**: 2026-04-05
> **버전**: v0.6.3 → v0.7.0

## TL;DR

번역 모델을 `gemma-3-27b-it`에서 `gemma-4-31b-it`(Dense)로 업그레이드. A/B 테스트 결과 `gemma-4-26b-a4b-it`(MoE)은 Google AI Studio API에서 100% 실패하여 탈락.

## 배경

### 변경 전

| 항목        | 값               |
| ----------- | ---------------- |
| SDK         | google-genai 1.56.0 |
| Aperture 모델 | gemma-3-12b-it  |
| AI Studio 모델 | gemma-3-27b-it  |
| API 패턴    | `client.models.generate_content(model, contents)` |

### 변경 후

| 항목        | 값               |
| ----------- | ---------------- |
| SDK         | google-genai >=1.70.0 |
| Aperture 모델 | gemma-4-31b-it  |
| AI Studio 모델 | gemma-4-31b-it  |
| API 패턴    | `client.models.generate_content(model, contents)` (동일) |

### Gemma-4-31b-it 스펙

| 항목            | 값                     |
| --------------- | ---------------------- |
| 총 파라미터     | 30.7B                  |
| 레이어          | 60                     |
| 컨텍스트        | 256K                   |
| MMLU Pro        | 85.2%                  |
| MMMLU           | 88.4%                  |
| 어휘            | 262K                   |
| 지원 언어       | 140+                   |

## A/B 테스트 결과 (260404_raw.yaml)

| 소스              | gemma-4-26b-a4b-it (MoE) | gemma-4-31b-it (Dense) |
| ----------------- | ------------------------ | ---------------------- |
| Nhân Dân          | ❌ 서버 연결 끊김 60s    | ✅ 1기사 22.4s          |
| Sức khỏe & Đời sống | ❌ 서버 연결 끊김 60s    | ❌ 서버 연결 끊김 60s   |
| Tuổi Trẻ          | ❌ 서버 연결 끊김 60s    | ✅ 1기사 33.3s          |
| VietnamNet        | ❌ 서버 연결 끊김 60s    | ✅ 2기사 50.9s          |
| VnExpress         | ❌ 서버 연결 끊김 60s    | ✅ 2기사 36.1s          |
| Thanh Niên        | ❌ 서버 연결 끊김 60s    | ❌ 서버 연결 끊김 60s   |
| VnExpress IT/과학 | ❌ 서버 연결 끊김 60s    | ✅ 2기사 32.7s          |
| **성공률**        | **0/7 (0%)**             | **5/7 (71%)**          |

- MoE 모델은 Google AI Studio API에서 완전히 작동 불가 (전체 요청 타임아웃)
- Dense 모델 2건 실패는 기사 수 과다(4-5개)로 인한 타임아웃. 기존 `with_api_retry()`로 커버 가능
- 번역 품질: 자연스러운 한국어 문장체, 정확한 용어 번역 확인

## 변경 내역

### 1. `translator.py` — 기본 모델명 변경

```python
# Before
model = os.getenv("APERTURE_MODEL", "gemma-3-12b-it")
model = os.getenv("GEMINI_MODEL", "gemma-3-27b-it")

# After
model = os.getenv("APERTURE_MODEL", "gemma-4-31b-it")
model = os.getenv("GEMINI_MODEL", "gemma-4-31b-it")
```

### 2. `pyproject.toml` — SDK 버전 상향

```toml
# Before
"google-genai==1.56.0",

# After
"google-genai>=1.70.0",
```

### 3. `.ai/CONTEXT.md` — 모델 스펙 업데이트

Gemma-3-27b-it → Gemma-4-31b-it (3곳)

## 롤백 계획

환경변수를 이전 값으로 복원:

```bash
APERTURE_MODEL=gemma-3-12b-it
GEMINI_MODEL=gemma-3-27b-it
```

코드 변경이 2줄(기본값)이므로 즉시 롤백 가능.

## 마일스톤

1. ~~SDK 업그레이드~~: `google-genai` 1.70.0 설치 확인 ✅
2. ~~모델 기본값 변경~~: `translator.py` 수정 완료 ✅
3. ~~문서 업데이트~~: CONTEXT.md 갱신 완료 ✅
4. ~~A/B 테스트~~: gemma-4-31b-it 단독 채택 확정 ✅
5. **v0.7.0 릴리즈**: 버전 업 및 커밋 대기
