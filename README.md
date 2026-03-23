# 오늘의 베트남 뉴스 (today-vn-news)

> **AI** 를 활용해 생성된 프로젝트입니다.

베트남 뉴스 자동화 파이프라인. BeautifulSoup4 스크래핑 + **Tailscale AI Gateway**(Gemma-3) 번역 + TTS(Edge/Qwen) 음성 생성 + FFmpeg 영상 합성 + YouTube 업로드.

## 📺 생성된 콘텐츠

[👉 유튜브 플레이리스트](https://www.youtube.com/playlist?list=PLzMxB6D1eypIA_JNasD_MNISMEUtMbHvK)

## 🏗️ 아키텍처

```
스크래핑 → 번역(Gemma-3) → TTS → 영상 합성 → YouTube 업로드 → Media 저장
```

## 📂 프로젝트 구조

```
today-vn-news/
├── main.py                # 엔트리포인트
├── today_vn_news/
│   ├── scraper.py         # 뉴스 스크래핑
│   ├── translator.py      # 베트남어 → 한국어 번역
│   ├── tts/               # TTS (Edge/Qwen)
│   ├── engine.py          # FFmpeg 영상 합성
│   ├── uploader.py        # YouTube 업로드
│   ├── video_source/      # 영상 소스 관리
│   └── notifications/     # Pushover 알림
├── tests/                 # pytest 테스트
├── data/                  # YAML/MP3/MP4 출력
└── assets/                # 배경 이미지 등
```

## 🚀 시작하기

```bash
# 1. 환경 설정
cp .env.example .env
# .env 파일에 API 키 설정: GEMINI_API_KEY, IQAIR_API_KEY

# 2. 의존성 설치
uv sync

# 3. 실행
uv run python main.py              # 현재 시간, Edge TTS
uv run python main.py 20260210     # 특정 날짜
uv run python main.py --tts=qwen   # Qwen3-TTS
uv run python main.py --help       # 사용법
```

### TTS 엔진

| 엔진 | 장점 | 음성 |
|------|------|------|
| **edge** (기본) | 빠름, 고품질 | ko-KR-SunHiNeural 등 |
| **qwen** | 오프라인, 무료, VoiceDesign | Sohee, Vivian, Serena 등 9개 |

**상세:** [docs/tts.md](docs/tts.md) (Qwen3-TTS 음성 목록, CustomVoice 설정)

## 🧪 테스트

```bash
uv run pytest                      # 전체 테스트
uv run pytest tests/unit/test_scraper.py -v    # 스크래핑
uv run pytest tests/unit/test_tts.py -v        # TTS
```

## ⚖️ 라이선스

MIT License - Copyright (c) 2026 Crong
