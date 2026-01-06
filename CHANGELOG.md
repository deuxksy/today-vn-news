# Changelog

## [0.1.11] - 2026-01-06

### Added

- `TODO.md` 도입: 향후 구현 과제 및 마일스톤 관리 체계 구축.

## [0.1.10] - 2026-01-06

### Changed

- 릴리즈 정책 고도화: Git 태그(`tag`) 생성 기준을 GitHub Release와 동일하게 `0.x.0` 버전으로 단일화. (`0.0.x`는 태그 미생성)

## [0.1.9] - 2026-01-06

### Changed

- Git 운영 정책 보완: `git push` 명령어는 다른 명령어와 조합하지 않고 단독으로 실행하도록 지침 수정.

## [0.1.8] - 2026-01-06

### Changed

- 구조적 제약 완화: '7-Files' 고정 제약을 제거하고 'Ultra-light' 관리 철학 유지로 변경.

## [0.1.7] - 2026-01-06

### Changed

- AI 작업 권한 전면 시행: `ContextFile.md` 제외 모든 파일(`README.md` 포함) 및 로컬 Git 작업(`add`, `commit`) 자율화.
- Git 운영 정책 확정: 수시 커밋은 AI가 담당, 푸시(`push`)만 사용자 승인 체계로 고정.

## [0.1.6] - 2026-01-06

### Changed

- `ContextFile.md` 전면 재작성: 비즈니스 도메인, 로직 우선순위 및 기기별 역할 상세 정의.
- `README.md` 개선: 불필요한 서술형 문구 제거 및 팩트 중심의 간결한 구조로 변경.

## [0.1.5] - 2026-01-06

### Changed

- Git 작업 정책 변경: 커밋(Commit)은 자율화하고 푸시(Push) 시에만 사용자 승인 요청.

## [0.1.4] - 2026-01-06

### Changed

- AI 자율 작업 권한 확대: `ContextFile.md` 제외 모든 작업에 대해 사용자 승인 절차 생략.

## [0.1.3] - 2026-01-06

### Changed

- 릴리즈 정책 변경: 0.0.x 패치 버전은 GitHub Release 자동 생성 제외 (0.x.0 이상만 수행).
- `GEMINI.md`에 새로운 릴리즈 및 Git 가이드라인 반영.

## [0.1.2] - 2026-01-06

### Changed

- `GEMINI.md` 프로젝트 실행 가이드 업데이트 (Vibe Coding 철학 및 운영 원칙 강화).
- Git 커밋 메시지 한국어 작성 원칙 명문화.

## [0.1.1] - 2026-01-06

### Changed

- GitHub Repository Description 및 Topics 설정 완료.
- 프로젝트 로그 정책 변경 (activity.log 삭제 및 CHANGELOG 중심 관리).

## [0.1.0] - 2026-01-06

### Added

- 프로젝트 초기화 및 표준 6파일 구조 확정.
- Human/AI 문서 분리 (README.md vs ContextFile.md).
- 독립된 CHANGELOG 관리 체계 구축.
- 콘텐츠 큐레이션 우선순위 설정 (건강/IT/로컬).