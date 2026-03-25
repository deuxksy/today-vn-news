#!/usr/bin/env python3
"""
예외 클래스 유닛 테스트
- 목적: 커스텀 예외 타입이 올바르게 정의되었는지 검증
"""

import pytest
from today_vn_news.exceptions import TodayVnNewsError, PipelineRestartError


def test_media_exceptions_exist():
    """
    Media 관련 예외 타입 4개가 올바르게 import되고 TodayVnNewsError를 상속하는지 확인.

    테스트 항목:
        - MediaMountError: Media 마운트 실패
        - MediaCopyError: Media 파일 복사 실패
        - MediaArchiveError: Media 저장 실패
        - VideoSourceError: 영상 소스 탐색 실패
    """
    from today_vn_news.exceptions import (
        MediaMountError,
        MediaCopyError,
        MediaArchiveError,
        VideoSourceError
    )

    # 각 예외가 인스턴스 가능한지 확인
    err1 = MediaMountError("test")
    err2 = MediaCopyError("test")
    err3 = MediaArchiveError("test")
    err4 = VideoSourceError("test")

    # 모든 예외가 TodayVnNewsError를 상속하는지 검증
    assert isinstance(err1, TodayVnNewsError)
    assert isinstance(err2, TodayVnNewsError)
    assert isinstance(err3, TodayVnNewsError)
    assert isinstance(err4, TodayVnNewsError)


def test_pipeline_restart_error():
    """PipelineRestartError should be instantiable with message"""
    error = PipelineRestartError("선행 단계가 완료되지 않았습니다")
    assert str(error) == "선행 단계가 완료되지 않았습니다"
    assert isinstance(error, TodayVnNewsError)
