#!/usr/bin/env python3
"""
커스텀 예외 클래스
- 목적: 모듈별 특화된 예외 처리를 위한 예외 계층 구조
"""


class TodayVnNewsError(Exception):
    """베이스 예외 클래스 - 프로젝트 전체 예외의 기본"""
    pass


class ScrapingError(TodayVnNewsError):
    """스크래핑 실패 시 발생"""
    pass


class TranslationError(TodayVnNewsError):
    """번역 실패 시 발생"""
    pass


class TTSError(TodayVnNewsError):
    """TTS 변환 실패 시 발생"""
    pass


class VideoSynthesisError(TodayVnNewsError):
    """영상 합성 실패 시 발생"""
    pass


class UploadError(TodayVnNewsError):
    """유튜브 업로드 실패 시 발생"""
    pass
