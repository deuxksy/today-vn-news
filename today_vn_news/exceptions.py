#!/usr/bin/env python3
"""
커스텀 예외 클래스
- 목적: 모듈별 특화된 예외 처리를 위한 예외 계층 구조
"""


class TodayVnNewsError(Exception):
    """
    베이스 예외 클래스.

    프로젝트 전체 예외의 기본 클래스입니다.
    모든 커스텀 예외는 이 클래스를 상속받습니다.

    Attributes:
        message: 예외 메시지

    Example:
        >>> raise TodayVnNewsError("일반적인 오류 발생")
    """
    pass


class ScrapingError(TodayVnNewsError):
    """
    스크래핑 실패 예외.

    RSS 피드 수집, 웹 스크래핑 실패 시 발생합니다.

    Attributes:
        message: 예외 메시지
        url: 실패한 URL (선택 사항)

    Example:
        >>> raise ScrapingError("RSS 피드 파싱 실패: https://example.com/feed")
    """
    pass


class TranslationError(TodayVnNewsError):
    """
    번역 실패 예외.

    텍스트 번역 과정에서 오류 발생 시 사용합니다.
    (현재 프로젝트에서는 비활성화된 기능)

    Example:
        >>> raise TranslationError("번역 API 호출 실패")
    """
    pass


class TTSError(TodayVnNewsError):
    """
    TTS 변환 실패 예외.

    텍스트 음성 변환 과정에서 오류 발생 시 사용합니다.
    Edge-TTS API 호출 실패, 오디오 파일 생성 실패 등을 포함합니다.

    Attributes:
        message: 예외 메시지
        text: 변환 실패한 텍스트 (선택 사항)

    Example:
        >>> raise TTSError("TTS 변환 실패: API 연결 오류")
    """
    pass


class VideoSynthesisError(TodayVnNewsError):
    """
    영상 합성 실패 예외.

    FFmpeg를 이용한 영상 합성 과정에서 오류 발생 시 사용합니다.
    오디오/비디오 파일 결합 실패, 인코딩 오류 등을 포함합니다.

    Attributes:
        message: 예외 메시지
        input_files: 처리 실패한 입력 파일 목록 (선택 사항)

    Example:
        >>> raise VideoSynthesisError("영상 합성 실패: FFmpeg 오류")
    """
    pass


class UploadError(TodayVnNewsError):
    """
    유튜브 업로드 실패 예외.

    YouTube API를 통한 영상 업로드 과정에서 오류 발생 시 사용합니다.
    인증 실패, quota 초과, 네트워크 오류 등을 포함합니다.

    Attributes:
        message: 예외 메시지
        video_path: 업로드 실패한 영상 파일 경로 (선택 사항)

    Example:
        >>> raise UploadError("유튜브 업로드 실패: 인증 토큰 만료")
    """
    pass


class MediaMountError(TodayVnNewsError):
    """
    Media 마운트 실패 예외.

    지정된 Media 경로가 존재하지 않거나 접근 불가능할 때 발생.

    Attributes:
        message: 예외 메시지
        media_path: 마운트 실패한 Media 경로 (선택 사항)

    Example:
        >>> raise MediaMountError("Media 경로 접근 실패: /Volumes/Media")
    """
    pass


class MediaCopyError(TodayVnNewsError):
    """
    Media 파일 복사 실패 예외.

    Media에서 로컬로 소스 영상 복사 실패 시 발생.

    Attributes:
        message: 예외 메시지
        source: 복사하려던 소스 파일 경로 (선택 사항)
        destination: 복사 대상 경로 (선택 사항)

    Example:
        >>> raise MediaCopyError("Media 파일 복사 실패: 디스크 공간 부족")
    """
    pass


class MediaArchiveError(TodayVnNewsError):
    """
    Media 저장 실패 예외.

    최종 영상을 Media로 이동/저장 실패 시 발생.

    Attributes:
        message: 예외 메시지
        video_path: 저장 실패한 영상 파일 경로 (선택 사항)
        target_dir: 저장하려던 Media 대상 경로 (선택 사항)

    Example:
        >>> raise MediaArchiveError("Media 아카이빙 실패: 쓰기 권한 없음")
    """
    pass


class VideoSourceError(TodayVnNewsError):
    """
    영상 소스 탐색 실패 예외.

    모든 우선순위 체인에서 소스를 찾을 수 없을 때 발생.

    Attributes:
        message: 예외 메시지
        searched_paths: 검색한 경로 목록 (선택 사항)

    Example:
        >>> raise VideoSourceError("영상 소스를 찾을 수 없음: 모든 경로 실패")
    """
    pass


class PipelineRestartError(TodayVnNewsError):
    """
    파이프라인 재시작 필요 예외.

    선행 단계의 완료 파일(.done)이 누락된 경우 발생합니다.
    사용자가 관련 파일을 삭제하고 처음부터 다시 실행해야 합니다.

    Attributes:
        message: 예외 메시지
        missing_stage: 완료 파일이 누락된 선행 단계 (선택 사항)

    Example:
        >>> raise PipelineRestartError("선행 단계가 완료되지 않았습니다")
    """
    pass
