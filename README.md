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

## 🎯 콘텐츠 큐레이션 우선순위

1. **건강 및 안전:** 궤양성 대장염 식단, 호치민 대기질 및 알레르기(오리풀).
2. **IT 및 경제:** 베트남 Java/Spring 시장 동향, AWS 클라우드.
3. **로컬 뉴스:** 호치민 시정 및 주요 로컬 이벤트.

## 📂 리포지토리 구조

```text
today-vn-news/
├── README.md           # 프로젝트 가이드
├── ContextFile.md      # 도메인 지식 및 기술 제약 (AI용)
├── CHANGELOG.md        # 버전 관리 및 변경 이력
├── LICENSE             # MIT License
├── .gitignore          # Git 제외 목록
├── main.py             # MD 파싱 + TTS + FFmpeg 통합 실행 엔진
└── requirements.txt    # 의존성 패키지
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
