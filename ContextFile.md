# ContextFile: today-vn-news

본 문서는 프로젝트 'today-vn-news'의 도메인 지식, 비즈니스 로직 및 기술적 제약 사항을 정의한다.

## 1. 비즈니스 도메인 및 데이터 소스

### 1.1 데이터 원천
- 직접적인 웹 스크래핑을 수행하지 않으며, 'Gemini Deep Research'를 통해 생성된 `YYMMDD.md` 마크다운 파일을 유일한 입력 데이터로 사용한다.

### 1.2 주요 뉴스 소스 (7대 일간지)
- VnExpress, Tuổi Trẻ, Thanh Niên, Sức khỏe & Đời sống, ICTNews, The Saigon Times, Nhân Dân.

## 2. 콘텐츠 큐레이션 및 로직 우선순위

데이터 파싱 및 TTS/영상 생성 시 다음 우선순위를 엄격히 준수한다.

### 1순위: 건강 및 안전 (Personal Health)
- **대상:** 궤양성 대장염(UC) 환자용 식품 위생 및 식단 정보.
- **환경:** 호치민 대기질, 알레르기(오리풀 등) 유발 요소 정보.
- **로직:** 관련 키워드 발견 시 최상단 배치 및 영상의 메인 뉴스로 처리.

### 2순위: IT 및 경제 (Professional)
- **키워드:** Java, Spring, AWS, Cloud, 호치민 개발자 채용 동향.
- **로직:** 베트남 내 IT 기술 시장의 흐름을 요약하여 중반부 배치.

### 3순위: 로컬 뉴스 (Local/Social)
- **대상:** 호치민 시정 소식, 주요 교통 통제, 랜드마크 2 등 주요 지역 이벤트.
- **로직:** 생활 밀착형 정보를 후반부 배치.

## 3. 인프라 및 기술 스펙 (Distributed Infrastructure)

### 3.1 기기별 역할 정의
- **N100 NAS (Fedora):** `Inotify`를 통한 파일 감시 및 원시 데이터 저장.
- **Steam Deck (SteamOS):** `edge-tts` 기반 음성 생성 및 `FFmpeg` 하드웨어 가속(`h264_vaapi`) 합성.
- **Mac Mini M4 (macOS):** 고해상도 렌더링 가속 테스트(`h264_videotoolbox`) 및 로직 고도화 개발.

### 3.2 핵심 기술 스택
- **Language:** Python 3.10+
- **TTS:** edge-tts (Voice: `vi-VN-HoaiMyNeural` 또는 `vi-VN-NamMinhNeural`)
- **Video:** FFmpeg (VAAPI/VideoToolbox 기반 하드웨어 인코딩)

## 4. 운영 가이드라인 (Vibe Coding Principles)
- **KISS (Keep It Simple, Stupid):** 초기 MVP 단계에서 불필요한 클래스 추상화보다 기능 구현에 집중한다.
- **Efficiency:** 24시간 가동되는 Steam Deck의 자원을 효율적으로 사용하도록 배치 프로세스를 설계한다.
- **Safety:** 사용자의 건강(궤양성 대장염)과 직결된 정보 누락을 방지하기 위한 필터링 로직을 최우선으로 검증한다.