# Qwen3-TTS 빠른 테스트 가이드

## 🚀 빠른 시작

### 1. 기본 사용법

```bash
# 텍스트와 음성 스타일 지정
python tests/unit/test_qwen_quick.py "안녕하세요! 반가워요~" "밝은 정중한 아나운서 목소리"
```

### 2. 다양한 음성 테스트

```bash
# 한국어 (Sohee - 기본)
python tests/unit/test_qwen_quick.py "안녕하세요! 오늘의 베트남 뉴스입니다." "따뜻한 아나운서 음성"

# 한국어 (다른 스타일)
python tests/unit/test_qwen_quick.py "안녕하세요!" "슬픈 목소리" --voice Sohee
python tests/unit/test_qwen_quick.py "안녕하세요!" "기쁜 목소리" --voice Sohee
python tests/unit/test_qwen_quick.py "안녕하세요!" "화난 목소리" --voice Sohee

# 영어
python tests/unit/test_qwen_quick.py "Hello! Nice to meet you." "Cheerful tone" --voice Aiden --language English
python tests/unit/test_qwen_quick.py "Hello!" "Sad tone" --voice Serena --language English

# 일본어
python tests/unit/test_qwen_quick.py "こんにちは！" "明るい女性の声" --voice Ono_Anna --language Japanese

# 중국어
python tests/unit/test_qwen_quick.py "你好！" "温柔的女声" --voice Vivian --language Chinese
python tests/unit/test_qwen_quick.py "你好！" "生气的声音" --voice Uncle_Fu --language Chinese
```

### 3. 음성 목록 확인

```bash
# 사용 가능한 음성 목록 출력
python tests/unit/test_qwen_quick.py --list-voices
```

### 4. 고급 옵션

```bash
# 재생 없이 파일만 생성
python tests/unit/test_qwen_quick.py "테스트" "스타일" --no-play

# 출력 파일 지정
python tests/unit/test_qwen_quick.py "테스트" "스타일" --output my_test.mp3

# 다른 모델 사용 (1.7B)
python tests/unit/test_qwen_quick.py "테스트" "스타일" --model Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign
```

---

## 📝 사용 예시

### 뉴스 아나운서 스타일

```bash
python tests/unit/test_qwen_quick.py \
  "오늘의 베트남 뉴스입니다. 호치민시 날씨는 맑고 기온은 32 도입니다." \
  "차분하고 전문적인 뉴스 아나운서 음성"
```

### 감정 표현 테스트

```bash
# 기쁨
python tests/unit/test_qwen_quick.py "정말 기쁜 소식입니다!" \
  "기쁘고 신나는 목소리, 톤 높게" --voice Sohee

# 슬픔
python tests/unit/test_qwen_quick.py "안타까운 소식이 전해졌습니다." \
  "슬프고 낮은 목소리" --voice Sohee

# 분노
python tests/unit/test_qwen_quick.py "이는 용납할 수 없는 일입니다!" \
  "화난 목소리, 강하게" --voice Sohee

# 공포
python tests/unit/test_qwen_quick.py "조심하세요! 위험합니다!" \
  "겁에 질린 목소리, 떨리는 톤" --voice Sohee
```

### 캐릭터별 테스트

```bash
# 어린 소녀
python tests/unit/test_qwen_quick.py "오빠! 놀러와!" \
  "어린 소녀의 귀여운 목소리, 톤 높게" --voice Ono_Anna --language Japanese

# 중년 남성
python tests/unit/test_qwen_quick.py "안녕하십니까." \
  "중년 남성의 낮고 안정적인 목소리" --voice Uncle_Fu --language Chinese

# 젊은 여성
python tests/unit/test_qwen_quick.py "Hello everyone!" \
  "젊은 여성의 밝고 경쾌한 목소리" --voice Vivian --language English
```

### 언어별 인사말 테스트

```bash
# 한국어
python tests/unit/test_qwen_quick.py "안녕하세요! 반가워요~" \
  "밝은 정중한 아나운서 목소리" --voice Sohee --language Korean

# 영어
python tests/unit/test_qwen_quick.py "Hi there! How are you today?" \
  "Friendly casual tone" --voice Aiden --language English

# 일본어
python tests/unit/test_qwen_quick.py "こんにちは！今日もいい一日を！" \
  "元気な女性の声" --voice Ono_Anna --language Japanese

# 중국어
python tests/unit/test_qwen_quick.py "大家好！今天天气真好！" \
  "温柔的女声" --voice Serena --language Chinese
```

---

## 🎯 팁

### 1. `instruct` 파라미터 활용

자연어로 음성 스타일을 자세히 설명할수록 좋은 결과가 나옵니다.

```bash
# 간단한 설명
python test_qwen_quick.py "테스트" "밝은 목소리"

# 자세한 설명 (추천)
python test_qwen_quick.py "테스트" "20 대 여성의 밝고 경쾌한 목소리, 톤을 조금 높여서"
```

### 2. 언어별 최적의 음성 사용

| 언어 | 추천 음성 |
|------|-----------|
| 한국어 | Sohee |
| 영어 (미국) | Aiden |
| 영어 (영국) | - |
| 일본어 | Ono_Anna |
| 중국어 | Vivian, Serena, Uncle_Fu |

### 3. 재생 속도 조절

```bash
# 빠른 재생 (1.5 배)
afplay -r 1.5 file.mp3

# 느린 재생 (0.5 배)
afplay -r 0.5 file.mp3
```

---

## ⚠️ 주의사항

- **첫 실행**: 모델 다운로드 시간 소요 (2-3GB, 5-10 분)
- **생성 시간**: 문장당 2-3 분 (M4 기준)
- **발열**: 장시간 실행 시 팬 소음 발생
- **메모리**: 약 2.5GB 사용

---

## 🔧 문제 해결

### `qwen-tts` 모듈 없음

```bash
uv sync --extra qwen
```

### MPS 오류 발생

```bash
# CPU 모드로 강제
export PYTORCH_ENABLE_MPS_FALLBACK=1
```

### 메모리 부족

```bash
# 다른 앱 종료 후 재시도
# 또는 1.7B 모델 대신 0.6B 사용 (기본값)
```
