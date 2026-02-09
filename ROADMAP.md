# 🚀 today-vn-news 장기 로드맵 (ROADMAP)

> **Goal:** `ContextFile.md`의 비즈니스 로직을 완벽히 구현한 뉴스 자동화 파이프라인 완성  

## 1단계: 뉴스 및 안전 데이터 수집 (Collection)

- [x] **기본 IT 뉴스 수집**: Google GenAI SDK를 통해 ICTNews 데이터 요약 및 YAML 저장
- [x] **안전 및 기상 관제**: 호치민 날씨, AQI(미세먼지) 수집 및 마스크 권고 로직 구현 (Gemma-3-27b)
- [x] **수집 대상**:  
  - [x] **NCHMF - 호치민 지역 특화 기상 정보**
  - [x] **IGP-VAST - 지진 및 쓰나미 속보 섹션**
  - [x] **IQAir - 공기질 정보(Ho Chi Minh City)**
  - [x] **Nhân Dân - 정부 공식 입장**
  - [x] **Sức khỏe & Đời sống - 건강 관련 이슈**
  - [x] **Tuổi Trẻ - 시정 소식**
  - [ ] **VN Express - 종합 뉴스**
- [x] **TTS 최적화 가이드라인 적용**: 에모지, 특수문자, 불필요한 영어 제거 필터링 구현

## 2단계: 음성 및 텍스트 최적화 (Voice & Text)

- [x] **TTS 변환**: `edge-tts` 기반 한국어 음성 생성
- [x] **텍스트 정제**: 마크다운 문법 및 특수문자 제거 로직 고도화

## 3단계: 분산 인프라 기반 영상 합성 (Video)

- [x] **하드웨어 가속 최적화**: Mac Mini(VideoToolbox) 및 Steam Deck(VAAPI) 옵션 구현
- [x] **오디오 믹싱**: 원본 영상 소리 제거 및 TTS 음성 정밀 합성 (길이 동기화 포함)
- [x] **동적 길이 조정**: TTS 오디오 길이에 맞춘 영상 소스 루프/컷 처리

## 4단계: 배포 및 보안 (Deployment & Security)

- [x] **YouTube API 통합**: OAuth 2.0 기반 자동 업로드 모듈 구현 (인증 대기)
- [x] **보안 강화**: `.env` 및 `client_secrets.json` 노출 방지 처리
- [x] **Release 정책**: 주요 단계 완료 시 GitHub Release(`v0.x.0`) 생성 자동화

## 5단계: 운영 지연 및 자동화 (Operations)

---
