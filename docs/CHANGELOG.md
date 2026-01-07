# Changelog

## [0.5.0] - 2026-01-07 [GitHub]

### Changed

- **아키텍처 개선**: `gemini` CLI 방식에서 직접 API 호출 방식으로 전환하여 성능 및 비용 효율성 대폭 향상.
  - 응답 시간: 180초 → 10초 (18배 개선)
  - 토큰 사용량: 99% 절감 (프로젝트 컨텍스트 자동 로딩 제거)
- **모델 변경**: `gemini-1.5-flash` → `gemini-2.0-flash-exp`
- **수집 모듈 리팩토링**: `collector.py`의 `fetch_source_content`와 `check_gemini_health`를 `requests` 라이브러리 기반으로 재작성.

### Added

- `requests` 라이브러리 의존성 추가 (`requirements.txt`)
- API 직접 호출 기반 헬스 체크 (`tests/debug_gemini.py`)

## [0.4.1] - 2026-01-06 [Internal]

### Changed

- **Linux/Steam Deck 최적화**: `engine.py`의 VAAPI 가속 로직을 개선하여 SteamOS 호환성 확보 (`-vaapi_device` 플래그 추가).
- **파이프라인 완전 가동**: `main.py`의 유튜브 업로드 로직 주석 해제 및 정식 활성화.
- **문서 정합성 수정**: `ContextFile.md` 구조 변경(4장)에 발맞춰 Python 모듈 내 Docstring 참조 일괄 업데이트.

## [0.4.0] - 2026-01-06 [GitHub]

### Added

- **4단계 (Deployment & Security) 완료**: YouTube API 통합 및 보안 강화 로직 최종 반영.
- **7대 일간지 통합 수집**: `VnExpress`, `Tuổi Trẻ`, `Nhân Dân` 등 주요 매체 및 건강/안전 실시간 정보 수집 엔진 완성.
- **출력 품질 고도화**: 리포트 내 메타 정보 제거 및 마크다운 계층 구조(##, ###) 확립.

### Changed

- **수집 모듈 리팩토링**: 확장 가능한 `SOURCES` 구조 도입 및 `ContextFile.md` SOP 순서 동기화.
- **TTS 최적화**: 에모지 제거 및 독음 변환 로직 강화로 음성 합성 품질 개선.

## [0.3.3] - 2026-01-06 [Internal]

### Added

- **7대 일간지 통합 수집 구현**: `VnExpress`, `Tuổi Trẻ`, `Thanh Niên`, `Nhân Dân` 등 주요 매체 및 건강/안전 실시간 정보 수집 로직 완성.

### Changed

- **수집 모듈 전면 리팩토링**: `collector.py`를 확장 가능한 구조로 재설계하고, 우선순위 기반 수집 및 통합 리포트 생성 기능 추가.

## [0.3.1] - 2026-01-06 [Internal]

### Added

- **멀티 소스 가이드라인 확립**: `ContextFile.md`에 7대 주요 일간지 및 건강/안전 데이터 수집 상세 명세 추가.

### Changed

- **TTS 최적화 강화**: `tts.py`의 텍스트 정제 로직 고도화(에모지 및 특수문자 제거) 및 Gemini 추출 프롬프트 개선.
- **데이터 관리 개선**: `collector.py`에서 뉴스 파일 생성 시 메인 헤더 자동 추가 기능 구현.

## [0.3.0] - 2026-01-06 [GitHub]

### Added

- **3단계 (Video) 완료**: FFmpeg 하드웨어 가속 기반 영상 합성 엔진 (`engine.py`) 구현.
- **4단계 (Deployment) 진행**: 유튜브 업로드 모듈 (`uploader.py`) 및 전체 파이프라인 통합 (`main.py`).

### Changed

- 영상 합성 로직 고도화: 오디오 제거 및 TTS 길이 자동 동기화 기능 추가.
- 보안 강화: `.gitignore`를 통한 기밀 파일(json, pickle, env) 차단 및 Multi-OS 지원.

## [0.1.15] - 2026-01-06 [Internal]

### Changed

- 프로젝트 구조 리팩토링: Python 패키지 구조(`today_vn_news/`) 도입 및 소스 파일 이동.
- 진입점 분리: 루트 `main.py`를 통합 실행 엔트리포인트로 구성.

## [0.1.14] - 2026-01-06 [Internal]

### Changed

- 운영 정책 업데이트: 단순 시스템 조회 명령어(`ls`, `which`, `env`, `pwd` 등)를 AI 자율 실행 범위에 포함.

## [0.1.13] - 2026-01-06 [Internal]

### Added

- `collector.py` 구현: Gemini CLI를 활용한 IT 뉴스 자동 수집 모듈 개발 (7.1 상세 명세 준수).

## [0.1.12] - 2026-01-06 [Internal]

### Changed

- CHANGELOG 시각화 개선: GitHub Release 여부에 따른 버전 라벨링 도입 (`[GitHub]`, `[Internal]`, `[Tag]`).

## [0.1.11] - 2026-01-06 [Internal]

### Added

- `TODO.md` 도입: 향후 구현 과제 및 마일스톤 관리 체계 구축.

## [0.1.10] - 2026-01-06 [Internal]

### Changed

- 릴리즈 정책 고도화: Git 태그(`tag`) 생성 기준을 GitHub Release와 동일하게 `0.x.0` 버전으로 단일화. (`0.0.x`는 태그 미생성)

## [0.1.9] - 2026-01-06 [Tag]

### Changed

- Git 운영 정책 보완: `git push` 명령어는 다른 명령어와 조합하지 않고 단독으로 실행하도록 지침 수정.

## [0.1.8] - 2026-01-06 [Tag]

### Changed

- 구조적 제약 완화: '7-Files' 고정 제약을 제거하고 'Ultra-light' 관리 철학 유지로 변경.

## [0.1.7] - 2026-01-06 [Tag]

### Changed

- AI 작업 권한 전면 시행: `ContextFile.md` 제외 모든 파일(`README.md` 포함) 및 로컬 Git 작업(`add`, `commit`) 자율화.
- Git 운영 정책 확정: 수시 커밋은 AI가 담당, 푸시(`push`)만 사용자 승인 체계로 고정.

## [0.1.6] - 2026-01-06 [Tag]

### Changed

- `ContextFile.md` 전면 재작성: 비즈니스 도메인, 로직 우선순위 및 기기별 역할 상세 정의.
- `README.md` 개선: 불필요한 서술형 문구 제거 및 팩트 중심의 간결한 구조로 변경.

## [0.1.5] - 2026-01-06 [Internal]

### Changed

- Git 작업 정책 변경: 커밋(Commit)은 자율화하고 푸시(Push) 시에만 사용자 승인 요청.

## [0.1.4] - 2026-01-06 [Tag]

### Changed

- AI 자율 작업 권한 확대: `ContextFile.md` 제외 모든 작업에 대해 사용자 승인 절차 생략.

## [0.1.3] - 2026-01-06 [Tag]

### Changed

- 릴리즈 정책 변경: 0.0.x 패치 버전은 GitHub Release 자동 생성 제외 (0.x.0 이상만 수행).
- `GEMINI.md`에 새로운 릴리즈 및 Git 가이드라인 반영.

## [0.1.2] - 2026-01-06 [GitHub]

### Changed

- `GEMINI.md` 프로젝트 실행 가이드 업데이트 (Vibe Coding 철학 및 운영 원칙 강화).
- Git 커밋 메시지 한국어 작성 원칙 명문화.

## [0.1.1] - 2026-01-06 [GitHub]

### Changed

- GitHub Repository Description 및 Topics 설정 완료.
- 프로젝트 로그 정책 변경 (activity.log 삭제 및 CHANGELOG 중심 관리).

## [0.1.0] - 2026-01-06 [Internal]

### Added

- 프로젝트 초기화 및 표준 6파일 구조 확정.
- Human/AI 문서 분리 (README.md vs ContextFile.md).
- 독립된 CHANGELOG 관리 체계 구축.
- 콘텐츠 큐레이션 우선순위 설정 (건강/IT/로컬).