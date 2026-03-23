# TTS 설정 가이드

## TTS 엔진 비교

| 엔진 | 방식 | 장점 | 단점 | 음성 |
|------|------|------|------|------|
| **edge** (기본) | 클라우드 API | 빠름, 고품질 | 인터넷 필요, API 호출 | ko-KR-SunHiNeural 등 |
| **qwen** | 로컬 실행 | 오프라인, 무료, VoiceDesign | GPU 권장, 첫 실행 다운로드 (3-5GB) | Sohee, Vivian, Serena 등 9 개 |

## Edge TTS

### 사용 가능한 음성

```bash
# 한국어 음성
ko-KR-SunHiNeural    # 여성 (밝은 톤)
ko-KR-BongJinNeural  # 남성 (차분한 톤)
ko-KR-GyuNeural       # 남성 (따뜻한 톤)
ko-KR-JiMinNeural    # 여성 (차분한 톤)
```

### 실행 방법

```bash
# 기본값 (ko-KR-SunHiNeural)
uv run python main.py

# 음성 지정
uv run python main.py --voice=ko-KR-BongJinNeural
```

## Qwen3-TTS

### 모델 정보

- **모델:** `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice` (기본값)
- **메모리:** 약 2-3GB (1.7B 대비 60% 감소)
- **Mac M4** 최적화된 경량 모델

### 공식 음성 (9개)

| 음성명 | 언어 | 성별 | 설명 |
|--------|------|------|------|
| `Sohee` | ko | female | Warm Korean female voice with rich emotion |
| `Ryan` | en | male | Dynamic male voice with strong rhythmic drive |
| `Aiden` | en | male | Sunny American male voice with a clear midrange |
| `Ono_Anna` | ja | female | Playful Japanese female voice with a light, nimble timbre |
| `Vivian` | zh | female | Bright, slightly edgy young female voice |
| `Serena` | zh | female | Warm, gentle young female voice |
| `Uncle_Fu` | zh | male | Seasoned male voice with a low, mellow timbre |
| `Dylan` | zh | male | Youthful Beijing male voice with a clear, natural timbre |
| `Eric` | zh | male | Lively Chengdu male voice with a slightly husky brightness |

### 지원 언어

한국어, 영어, 일본어, 중국어, 독일어, 프랑스어, 러시아어, 포르투갈어, 스페인어, 이탈리아어

### 실행 방법

```bash
# 기본값 (Sohee)
uv run python main.py --tts=qwen

# 음성 지정
uv run python main.py --tts=qwen --voice=Vivian

# VoiceDesign (음성 스타일 지정)
uv run python main.py --tts=qwen --voice=Sohee --instruct="따뜻한 아나운서 음성으로 읽어주세요"

# 언어 지정
uv run python main.py --tts=qwen --voice=Aiden --language=English
```

### 음성 목록 확인 명령

```bash
# 전체 음성 목록 출력
python tests/unit/test_qwen_voices.py --list-voices

# 특정 언어만 출력 (ko, en, ja, zh 등)
python tests/unit/test_qwen_voices.py --list-voices --lang ko

# 특정 음성 테스트
python tests/unit/test_qwen_voices.py --voice Sohee

# 모든 음성 일괄 테스트
python tests/unit/test_qwen_voices.py --all
```

### Mac M4 실행 시 주의사항

- **MPS 백엔드 자동 사용**: `device_map="mps"`
- **발열**: 장시간 실행 시 열스로틀링 발생 가능
- **성능**: GPU에 비해 느림 (실시간 생성 권장 안함)
- **권장**: 클라우드 GPU 또는 DashScope API 사용

## 참고

- **출처:** [Qwen3-TTS GitHub](https://github.com/QwenLM/Qwen3-TTS)
