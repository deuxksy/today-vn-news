# 🇻🇳 오늘의 베트남 뉴스 (today-vn-news)

> **"Vibe Coding: AI와 함께 호흡하며 만드는 뉴스 자동화 파이프라인"**
> 본 프로젝트는 시니어 엔지니어의 아키텍처 설계와 AI의 빠른 구현력을 결합한 **Vibe Coding** 방식으로 제작되었습니다.

## 📋 프로젝트 개요

베트남 현지 7대 일간지의 뉴스를 수집(MD)하여, 분산 인프라를 통해 자동으로 영상을 제작하고 유튜브 채널 운영을 최적화하는 시스템입니다. 사용자의 건강 상태와 전문 분야를 고려한 맞춤형 큐레이션을 지향합니다.

## 🏗️ 분산 아키텍처 (Distributed Infrastructure)

효율적인 자원 활용을 위해 각 하드웨어의 특성에 맞게 역할을 분담합니다.

| 기기 | OS | 주요 역할 | 가속 기술 |
| :--- | :--- | :--- | :--- |
| **N100 NAS** | Fedora | 데이터 저장소 (Source Root), 파일 업로드 감시 | - |
| **Steam Deck** | SteamOS | 24/7 배치 서버, TTS 음성 생성, 영상 합성 | **VAAPI** |
| **Mac Mini M4** | macOS | 로직 개발, 고해상도 최종 렌더링 가속 | **VideoToolbox** |

## 🎯 콘텐츠 큐레이션 우선순위

뉴스 데이터(`YYMMDD.md`) 파싱 시 아래의 순서에 따라 가중치를 부여합니다.

1. **건강 및 안전 (1순위):** 궤양성 대장염 식단 관리, 호치민 대기질 및 알레르기(오리풀 등) 정보.
2. **IT 및 경제 (2순위):** 베트남 내 Java/Spring 개발 시장 동향, AWS 클라우드 소식.
3. **로컬 뉴스 (3순위):** 호치민 시정 소식 및 주요 로컬 이벤트.

## 📂 리포지토리 구조

초경량(Ultra-light)이면서도 관리 포인트가 명확한 7개 파일 구조를 유지합니다.

```text
today-vn-news/
├── README.md           # [Human] 프로젝트 가이드 및 현재 문서
├── ContextFile.md      # [AI] 페르소나, 기술 제약, 우선순위 (AI 전용 지침)
├── CHANGELOG.md        # [Release] 버전 관리 및 변경 이력 (독립 파일)
├── LICENSE             # [MIT] Copyright (c) 2026 Crong
├── .gitignore          # 리포지토리 위생 관리 (임시 파일 제외)
├── main.py             # [Core] MD 파서 + TTS + FFmpeg 통합 실행기
└── requirements.txt    # 의존성 관리 (edge-tts 등)
```

## 🚀 시작하기 (Quick Start)

1. **의존성 설치:**

```bash
pip install -r requirements.txt
```

1. **뉴스 처리 실행:**

```bash
python main.py --file YYMMDD.md
```

## ⚖️ 라이선스

MIT License - Copyright (c) 2026 Crong
