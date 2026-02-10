# 🇻🇳 오늘의 베트남 뉴스 (today-vn-news)

**Vibe Coding** 기반 베트남 뉴스 자동화 파이프라인. BeautifulSoup4 스크래핑 + Gemma-3-27b 번역 + edge-tts 음성 생성 + FFmpeg 영상 합성 + YouTube 업로드.

## 📋 프로젝트 개요

베트남 현지 10개 소스(안전/기상/정부/보건/종합/IT/정보통신/사회/경제) 뉴스 자동 수집 및 영상 제작 시스템. 사용자 건강(궤양성 대장염, 알레르기) 및 전문 분야(IT) 중심 큐레이션 제공.

## 🏗️ 분산 아키텍처 (Distributed Infrastructure)

| 기기 | OS | 주요 역할 | 가속 기술 |
| :--- | :--- | :--- | :--- |
| **N100 NAS** | Fedora | 데이터 저장소, 파일 업로드 감시 | - |
| **Steam Deck** | SteamOS | 24/7 배치 서버, TTS 음성 생성, 영상 합성 | **VAAPI** |
| **Mac Mini M4** | macOS | 로직 개발, 고해상도 최종 렌더링 가속 | **VideoToolbox** |

## 🔄 데이터 파이프라인

```text
1. 스크래핑 (scraper.py)
   └─> BeautifulSoup4 기반 10개 소스 수집
   └─> IQAir API + Open-Meteo API (공기질: AQI, PM2.5, PM10)
   └─> IGP-VAST RSS 피드 (지진 정보, 당일 필터링)
   └─> 원본 YAML 저장 (data/YYYYMMDD_HHMM_raw.yaml)

2. 번역 (translator.py)
   └─> Gemma-3-27b-it 기반 베트남어 → 한국어
   └─> 기상 상태 한글 번역 (사전 + API)
   └─> 번역된 YAML 저장 (data/YYYYMMDD_HHMM.yaml)

3. TTS 음성 생성 (tts.py)
   └─> edge-tts 기반 한국어 음성 변환
   └─> 특수문자/영어 제거 (TTS 최적화)
   └─> MP3 출력 (data/YYYYMMDD_HHMM.mp3)

4. 영상 합성 (engine.py)
   └─> FFmpeg 기반 오디오/비디오 믹스
   └─> 하드웨어 가속 (VideoToolbox/VAAPI)
   └─> 최종 영상 (data/YYYYMMDD_HHMM_final.mp4)

5. 유튜브 업로드 (uploader.py)
   └─> YouTube Data API v3
   └─> OAuth2 인증
```

## 🎯 데이터 소스 (10개)

| 소스 | 분류 | 우선순위 | 수집 방식 |
|:---|:---|:---|:---|
| **NCHMF** | 기상 | P0 | 스크래핑 (호치민 날씨) |
| **IQAir + Open-Meteo** | 공기질 | P0 | API (AQI, PM2.5, PM10) |
| **IGP-VAST** | 지진 | P0 | RSS 피드 (당일 필터링) |
| **Nhân Dân** | 정부 기관지 | P1 | 스크래핑 |
| **Sức khỏe & Đời sống** | 보건부 공식 | P0 | 스크래핑 |
| **Tuổi Trẻ** | 호치민 로컬 | P2 | 스크래핑 |
| **VietnamNet** | 종합 뉴스 | P2 | 스크래핑 (시사/경제) |
| **VnExpress** | 종합 뉴스 | P2 | 스크래핑 (시사/경제) |
| **Thanh Niên** | 사회/청년 | P2 | RSS 파싱 |
| **The Saigon Times** | 경제 | P2 | 스크래핑 |
| **VietnamNet 정보통신** | IT/통신 | P2 | 스크래핑 |
| **VnExpress IT/과학** | IT/과학 | P2 | 스크래핑 |

## 📂 리포지토리 구조

```text
today-vn-news/Claude/
├── README.md              # 프로젝트 가이드
├── ROADMAP.md             # 장기 로드맵
├── pyproject.toml         # uv 기반 프로젝트 설정 (Python 3.13+)
├── main.py                # 파이프라인 엔트리포인트
├── .ai/                   # AI 협업 설정
│   ├── AGENTS.md          # AI 실행 가이드
│   ├── CONTEXT.md         # 도메인 지식 (SSoT)
│   └── AI.ignore          # AI 무시 규칙
├── .claude/               # Claude Code 설정
│   └── settings.local.json # 권한 설정
├── today_vn_news/         # Core 패키지
│   ├── scraper.py         # 10개 소스 스크래핑 (1477 라인)
│   ├── translator.py      # Gemma 기반 번역 (393 라인)
│   ├── tts.py             # edge-tts 음성 변환
│   ├── engine.py          # FFmpeg 영상 합성
│   └── uploader.py        # YouTube 업로드
├── tests/                 # pytest 테스트
│   ├── conftest.py
│   └── (테스트 파일들)
├── data/                  # YAML/MP3/MP4 출력
├── assets/                # 배경 이미지 등
├── client_secrets.json    # [Git Ignored] YouTube OAuth
└── .env                   # [Git Ignored] API 키
```

## 🚀 시작하기

### 1. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# API 키 설정 (필수)
GEMINI_API_KEY=your_gemini_api_key_here
IQAIR_API_KEY=your_iqair_api_key_here

# YouTube 업로드 시 필요 (선택)
GOOGLE_API_KEY=your_google_api_key
```

### 2. 의존성 설치

```bash
# uv 설치 (없는 경우)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 프로젝트 의존성 설치
uv sync
```

### 3. 전체 파이프라인 실행

```bash
# 기본 실행 (현재 시간으로 자동 생성)
uv run python main.py

# 특정 날짜/시간 지정 (YYMMDD 또는 YYMMDD-HHMM)
uv run python main.py 20260210
uv run python main.py 20260210-1430
```

### 📺 실행 결과 예시 (Success Scenario)

성공적으로 실행될 경우 다음과 같은 파이프라인 흐름을 거칩니다:

 ```text
 ========================================
 🇻🇳 오늘의 베트남 뉴스 (today-vn-news)
 ========================================

 [*] 모든 소스 스크래핑 시작 (2026-01-12)
 --------------------------------------------------
 [스크래핑] NCHMF 기상 정보 수집 중...
   [DEBUG] NCHMF 페이지 구조 분석 중...
   [INFO] 기상 정보 추가됨: 맑음, 32°C
   [OK] NCHMF 기상 정보 수집 완료
 [스크래핑] IQAir 공기질 정보 수집 중...
   [INFO] 공기질 정보 추가됨: AQI 85, 양호
   [OK] IQAir 공기질 정보 수집 완료
 [스크래핑] IGP-VAST 지진 정보 수집 중...
   [OK] IGP-VAST: 0개 지진 정보 수집
 [스크래핑] Nhân Dân 수집 중...
   [OK] Nhân Dân: 0개 기사 수집
 [스크래핑] Sức khỏe & Đời sống 수집 중...
   [OK] Sức khỏe & Đời sống: 0개 기사 수집
 [스크래핑] Tuổi Trẻ 수집 중...
   [OK] Tuổi Trẻ: 0개 기사 수집
 [스크래핑] VietnamNet 종합 뉴스 수집 중...
   [OK] VietnamNet 종합 뉴스: 2개 기사 수집
 [스크래핑] VnExpress 수집 중...
   [OK] VnExpress: 2개 기사 수집
 [스크래핑] Thanh Niên 수집 중...
   [OK] Thanh Niên: 2개 기사 수집
 [스크래핑] The Saigon Times 수집 중...
   [OK] The Saigon Times: 2개 기사 수집
 --------------------------------------------------
 [+] 원본 YAML 저장 완료: data/20260112_1353_raw.yaml

 [*] 모든 뉴스 번역 시작...
 --------------------------------------------------
   [OK] 안전 및 기상 관제 데이터 저장 완료: 2개
   [번역] VietnamNet 종합 뉴스 기사 2개 번역 중...
   [OK] VietnamNet 종합 뉴스 번역 완료: 2개
   [번역] VnExpress 기사 2개 번역 중...
   [OK] VnExpress 번역 완료: 2개
   [번역] Thanh Niên 기사 2개 번역 중...
   [OK] Thanh Niên 번역 완료: 2개
   [번역] The Saigon Times 기사 2개 번역 중...
   [OK] The Saigon Times 번역 완료: 2개
   [번역] VietnamNet 정보통신 기사 2개 번역 중...
   [OK] VietnamNet 정보통신 번역 완료: 2개
   [번역] VnExpress IT/과학 기사 2개 번역 중...
   [OK] VnExpress IT/과학 번역 완료: 2개
 --------------------------------------------------
 [+] 번역된 YAML 저장 완료: data/20260112_1353.yaml

 [*] 3단계: TTS 음성 변환 시작...
 [*] YAML 파일 읽기 및 정제 시작: data/20260112_1353.yaml
 [*] TTS 변환 시작 (Voice: ko-KR-SunHiNeural)...
 [+] 음성 파일 생성 완료: data/20260112_1353.mp3

 [*] 4단계: 영상 합성(FFmpeg) 시작...
 [+] 최종 영상 생성 완료: data/20260112_1353_final.mp4

 [*] 5단계: 유튜브 업로드 시작...
 [+] 업로드 완료! Video ID: mgt8WtaVxB8
 [*] 재생 목록에 추가 중... [OK]

 🎉 모든 파이프라인 작업이 성공적으로 완료되었습니다!
 ========================================
 ```

## 📊 주요 기능 완료 현황 (v0.6.2)

- [x] **Step 1: Collection** - BeautifulSoup4 기반 10개 소스 스크래핑 + Gemma-3-27b-it 번역
- [x] **Step 2: Voice & Optimization** - YAML 파싱 기반 TTS 음성 최적화 (한국어 읽기)
- [x] **Step 3: Video** - FFmpeg 하드웨어 가속(VideoToolbox/VAAPI) 합성 최적화
- [x] **Step 4: Deployment** - 유튜브 API 통합 및 OAuth2 인증
- [ ] **Step 5: Operations** - NAS Inotify 감시 및 자동 스케줄링 (진행 예정)

## 🧪 테스트

### 실행 방법

```bash
# 전체 테스트 실행
uv run pytest

# 빠른 테스트 (외부 API 제외)
uv run pytest -m "not slow"

# 단위 테스트만
uv run pytest -m "unit"

# 통합 테스트만
uv run pytest -m "integration"

# 커버리지 확인
uv run pytest --cov=today_vn_news --cov-report=html
```

### 테스트 마커

| 마커 | 설명 |
|:---|:---|
| `unit` | 단위 테스트 |
| `integration` | 통합 테스트 |
| `slow` | 외부 API 호출 테스트 |
| `upload` | 유튜브 업로드 테스트 |

### 테스트 구조

```
tests/
├── conftest.py              # 공통 fixture
├── unit/                    # 단위 테스트
│   ├── test_scraper.py      # 스크래핑 테스트
│   ├── test_translator.py   # 번역 테스트
│   └── test_tts.py          # TTS 테스트
└── data/                    # 테스트 데이터
    └── test.yaml            # 테스트용 YAML
```

## ⚖️ 라이선스

MIT License - Copyright (c) 2026 Crong
