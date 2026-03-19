# Qwen3-TTS 테스트 가이드

## 📋 테스트 코드 목록

| 파일 | 설명 |
|------|------|
| `tests/unit/test_tts_qwen.py` | Qwen3-TTS 단위 테스트 (pytest) |
| `tests/unit/test_qwen_voices.py` | 음성 목록 확인 및 수동 테스트 |

---

## 🧪 pytest 테스트 실행

### 1. 기본 테스트 (음성 목록만 확인)

```bash
# 음성 목록 구조 테스트 (빠름, API 호출 없음)
uv run pytest tests/unit/test_tts_qwen.py::TestQwenVoices -v
```

**예상 출력:**
```
tests/unit/test_tts_qwen.py::TestQwenVoices::test_available_voices_structure PASSED
tests/unit/test_tts_qwen.py::TestQwenVoices::test_korean_voices PASSED
tests/unit/test_tts_qwen.py::TestQwenVoices::test_all_voices_have_required_fields PASSED
tests/unit/test_tts_qwen.py::TestQwenVoices::test_list_voices_output PASSED
```

### 2. 실제 TTS 생성 테스트 (느림, 모델 다운로드 필요)

```bash
# 전체 테스트 (0.6B 모델 다운로드 및 실행)
uv run pytest tests/unit/test_tts_qwen.py::TestQwenTTSRealAPI -v

# 특정 테스트만 실행
uv run pytest tests/unit/test_tts_qwen.py::TestQwenTTSRealAPI::test_yaml_to_tts_qwen_default_voice -v

# 한국어 음성 테스트
uv run pytest tests/unit/test_tts_qwen.py::TestQwenTTSRealAPI::test_yaml_to_tts_qwen_korean_voices -v

# 영어 음성 테스트
uv run pytest tests/unit/test_tts_qwen.py::TestQwenTTSRealAPI::test_yaml_to_tts_qwen_english_voices -v

# VoiceDesign (instruct) 테스트
uv run pytest tests/unit/test_tts_qwen.py::TestQwenTTSRealAPI::test_qwen_tts_with_instruct -v
```

### 3. 메모리 사용량 확인하며 테스트

```bash
# 별도 터미널에서 메모리 모니터링
watch -n 1 memory_pressure

# 다른 터미널에서 테스트 실행
uv run pytest tests/unit/test_tts_qwen.py::TestQwenTTSRealAPI::test_yaml_to_tts_qwen_default_voice -v
```

---

## 🔧 수동 테스트 스크립트

### 1. 음성 목록 확인

```bash
# 전체 음성 목록 출력
python tests/unit/test_qwen_voices.py --list-voices

# 특정 언어만 출력
python tests/unit/test_qwen_voices.py --list-voices --lang ko
python tests/unit/test_qwen_voices.py --list-voices --lang en
python tests/unit/test_qwen_voices.py --list-voices --lang zh
```

### 2. 단일 음성 테스트

```bash
# 한국어 음성 (Sohee)
python tests/unit/test_qwen_voices.py --voice Sohee --language Korean

# 영어 음성 (Aiden)
python tests/unit/test_qwen_voices.py --voice Aiden --language English

# 일본어 음성 (Ono_Anna)
python tests/unit/test_qwen_voices.py --voice Ono_Anna --language Japanese

# 중국어 음성 (Vivian)
python tests/unit/test_qwen_voices.py --voice Vivian --language Chinese
```

### 3. 모든 음성 일괄 테스트

```bash
# 9 개 음성 모두 테스트 (시간 소요)
python tests/unit/test_qwen_voices.py --all
```

---

## 📊 0.6B 모델 정보

| 항목 | 값 |
|------|-----|
| **모델명** | `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice` |
| **파라미터** | 0.6B (6 억) |
| **메모리** | 약 2-3 GB |
| **첫 실행** | 모델 다운로드 (약 2GB, 5-10 분) |
| **추론 속도** | 문장당 5-15 초 (M4 기준) |

---

## ⚠️ 주의사항

### Mac M4 에서 실행 시

1. **첫 실행**: 모델 다운로드 시간 소요 (2-3GB)
2. **발열**: 장시간 실행 시 팬 소음 발생
3. **메모리**: 2-3GB 사용 (16GB 시스템 권장)

### 테스트 실패 시

```bash
# 1. 의존성 재설치
uv sync --extra qwen

# 2. 캐시 삭제
rm -rf ~/Library/Caches/huggingface

# 3. Edge TTS 로 전환 (임시)
uv run python main.py --tts=edge
```

---

## 💡 권장 워크플로우

```bash
# 1. 빠른 구조 테스트 (API 호출 없음)
uv run pytest tests/unit/test_tts_qwen.py::TestQwenVoices -v

# 2. 단일 음성 테스트
uv run pytest tests/unit/test_tts_qwen.py::TestQwenTTSRealAPI::test_yaml_to_tts_qwen_korean_voices -v

# 3. 전체 테스트 (시간 여유 있을 때)
uv run pytest tests/unit/test_tts_qwen.py::TestQwenTTSRealAPI -v
```

---

## 📝 테스트 결과 예시

```
================================= test session starts =================================
platform darwin -- Python 3.13.0, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/crong/git/today-vn-news
plugins: asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 12 items

tests/unit/test_tts_qwen.py::TestQwenVoices::test_available_voices_structure PASSED   [  8%]
tests/unit/test_tts_qwen.py::TestQwenVoices::test_korean_voices PASSED                [ 16%]
tests/unit/test_tts_qwen.py::TestQwenVoices::test_all_voices_have_required_fields PASSED [ 25%]
tests/unit/test_tts_qwen.py::TestQwenVoices::test_list_voices_output PASSED           [ 33%]
tests/unit/test_tts_qwen.py::TestQwenTTSRealAPI::test_yaml_to_tts_qwen_default_voice PASSED [ 41%]
tests/unit/test_tts_qwen.py::TestQwenTTSRealAPI::test_yaml_to_tts_qwen_korean_voices PASSED [ 50%]
tests/unit/test_tts_qwen.py::TestQwenTTSRealAPI::test_yaml_to_tts_qwen_english_voices PASSED [ 58%]
tests/unit/test_tts_qwen.py::TestQwenTTSRealAPI::test_yaml_to_tts_qwen_japanese_voices PASSED [ 66%]
tests/unit/test_tts_qwen.py::TestQwenTTSRealAPI::test_yaml_to_tts_qwen_chinese_voices PASSED [ 75%]
tests/unit/test_tts_qwen.py::TestQwenTTSRealAPI::test_qwen_tts_with_instruct PASSED   [ 83%]

================================= 10 passed in 45.23s =================================
```
