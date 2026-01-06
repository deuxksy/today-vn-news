# 🇻🇳 오늘의 베트남 뉴스 (today-vn-news)

Vibe Coding 기반 뉴스 자동화 파이프라인.

## 📋 프로젝트 개요

베트남 현지 7대 일간지 뉴스 수집(MD) 및 분산 인프라 기반 영상 제작 자동화 시스템. 사용자 건강(UC) 및 전문 분야(IT) 중심 큐레이션 제공.

## 🏗️ 분산 아키텍처 (Distributed Infrastructure)

| 기기 | OS | 주요 역할 | 가속 기술 |
| :--- | :--- | :--- | :--- |
| **N100 NAS** | Fedora | 데이터 저장소, 파일 업로드 감시 | - |
| **Steam Deck** | SteamOS | 24/7 배치 서버, TTS 음성 생성, 영상 합성 | **VAAPI** |
| **Mac Mini M4** | macOS | 로직 개발, 고해상도 최종 렌더링 가속 | **VideoToolbox** |

## 🔄 시스템 아키텍처 및 데이터 흐름

```mermaid
graph TD
    subgraph "1. 데이터 수집 (Collection)"
        G[Gemini Research] -->|IT/건강/로컬| MD[data/YYMMDD.md]
    end

    subgraph "2. 처리 파이프라인 (main.py)"
        MD -->|Parsing| TTS[tts.py: edge-tts]
        TTS -->|V-Voice| MP3[data/YYMMDD.mp3]
        
        MP3 -->|Mixing| Engine[engine.py: FFmpeg]
        MOV[data/YYMMDD.mov] -->|Video Source| Engine
        
        Engine -->|Hardware Accel| Final[data/YYMMDD_final.mp4]
    end

    subgraph "3. 배포 (Deployment)"
        Final -->|OAuth2| UP[uploader.py: YouTube API]
        UP --> YT((YouTube Channel))
    end

    subgraph "💻 분산 인프라"
        NAS[N100 NAS: Inotify / Storage]
        SD[Steam Deck: VAAPI Synth]
        MAC[Mac Mini M4: VideoToolbox Dev]
    end

    MD -.-> NAS
    Final -.-> NAS
    Engine -.-> SD
    Engine -.-> MAC
```

## 🎯 콘텐츠 큐레이션 우선순위

1. **건강 및 안전:** 궤양성 대장염 식단, 호치민 대기질 및 알레르기(오리풀).
2. **IT 및 경제:** 베트남 Java/Spring 시장 동향, AWS 클라우드.
3. **로컬 뉴스:** 호치민 시정 및 주요 로컬 이벤트.

## 📂 리포지토리 구조

```text
today-vn-news/
├── README.md           # 프로젝트 가이드
├── ContextFile.md      # 도메인 지식 및 기술 제약 (AI용 SSoT)
├── CHANGELOG.md        # 버전 관리 및 변경 이력
├── TODO.md             # 단계별 작업 관리 (Step 1~5)
├── GEMINI.md           # AI 협업 지침 및 운영 정책
├── main.py             # 파이프라인 통합 실행 엔트리포인트
├── today_vn_news/      # Core 로직 패키지
│   ├── collector.py    # Gemini CLI 기반 뉴스 수집 모듈
│   ├── tts.py          # edge-tts 기반 음성 변환 모듈
│   ├── engine.py       # FFmpeg 기반 영상 합성 엔진
│   └── uploader.py     # YouTube Data API v3 업로드 모듈
├── client_secrets.json # (Secret) Google OAuth2 자격 증명 [Git Ignored]
├── .env                # (Secret) API 키 환경 변수 [Git Ignored]
└── requirements.txt    # 의존성 패키지 관리
```

## 🚀 시작하기 (Quick Start)

### 1. 환경 설정

`client_secrets.json` (유튜브 API) 및 `.env` (Gemini API 키) 파일을 프로젝트 루트에 준비합니다.

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 전체 파이프라인 실행

```bash
# 당일 뉴스 처리 (수집 -> TTS -> 합성 -> 업로드)
python main.py

# 특정 날짜 뉴스 처리
python main.py 260106
```

## 🛠️ 주요 기능 완료 현황

- [x] **Step 1: Collection** - VietnamNet, Nhân Dân 뉴스 수집 자동화
- [x] **Step 2: Voice** - edge-tts 기반 한국어 음성 생성 성공
- [x] **Step 3: Video** - FFmpeg 하드웨어 가속(VideoToolbox/VAAPI) 합성 완료
- [x] **Step 4: Deployment** - 유튜브 업로드 모듈 구현 완료 (현재 인증 대기 중)
- [ ] **Step 5: Operations** - NAS Inotify 감시 및 자동 스케줄링 예정

## ⚖️ 라이선스

MIT License - Copyright (c) 2026 Crong
