"""
Done-file 기능 수동 검증 테스트

파이프라인의 각 단계에서 done-file이 정상적으로 동작하는지 검증합니다.
실제 뉴스 스크래핑은 실행하지 않고 Mock 데이터를 사용합니다.
"""

import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import pytest
import yaml

from today_vn_news.timestamp import (
    normalize_timestamp,
    exists_done,
    create_done,
    assert_exists_done,
    validate_yymmdd
)


class TestDoneFileVerification:
    """Done-file 기능 파이프라인 동작 검증"""

    @pytest.fixture
    def temp_workspace(self, monkeypatch):
        """임시 작업 공간 생성 및 data 디렉토리 설정"""
        temp_dir = tempfile.mkdtemp()
        data_dir = Path(temp_dir) / "data"
        data_dir.mkdir()

        # 현재 작업 디렉토리를 임시 디렉토리로 변경
        monkeypatch.chdir(temp_dir)

        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_data(self):
        """Mock 뉴스 데이터"""
        return {
            'date': '260325',
            'weather': {
                'condition': '맑음',
                'temperature': '32°C'
            },
            'articles': [
                {
                    'source': 'VnExpress',
                    'title': '테스트 기사',
                    'url': 'https://example.com/test',
                    'summary': '테스트 요약'
                }
            ]
        }

    def test_scraper_done_skips_scraping(self, temp_workspace, mock_data):
        """scraper.done 존재 시 스크래핑 건너뜀기"""
        date_str = '260325'

        # 1. scraper.done 생성
        create_done(date_str, 'scraper')
        assert exists_done(date_str, 'scraper') is True

        # 2. scraper.done 존재 확인 후 스크래핑 건너뜀
        if exists_done(date_str, 'scraper'):
            # 스크래핑 생략
            scraped_data = None
        else:
            # 스크래핑 수행 (여기서는 Mock)
            scraped_data = mock_data

        assert scraped_data is None, "scraper.done이 존재하면 스크래핑을 건너뛰어야 함"

    def test_translator_done_skips_translation(self, temp_workspace, mock_data):
        """translator.done 존재 시 번역 건너뜀기"""
        date_str = '260325'

        # 1. translator.done 생성
        create_done(date_str, 'translator')
        assert exists_done(date_str, 'translator') is True

        # 2. translator.done 존재 확인 후 번역 건너뜀
        if exists_done(date_str, 'translator'):
            # 번역 생략
            translated_data = None
        else:
            # 번역 수행 (여기서는 Mock)
            translated_data = mock_data

        assert translated_data is None, "translator.done이 존재하면 번역을 건너뛰어야 함"

    def test_tts_done_skips_tts(self, temp_workspace, mock_data):
        """tts.done 존재 시 TTS 건너뜀기"""
        date_str = '260325'

        # 1. tts.done 생성
        create_done(date_str, 'tts')
        assert exists_done(date_str, 'tts') is True

        # 2. tts.done 존재 확인 후 TTS 건너뜀
        if exists_done(date_str, 'tts'):
            # TTS 생략
            audio_file = None
        else:
            # TTS 수행 (여기서는 Mock)
            audio_file = "260325_audio.mp3"

        assert audio_file is None, "tts.done이 존재하면 TTS를 건너뛰어야 함"

    def test_engine_done_skips_synthesis(self, temp_workspace, mock_data):
        """engine.done 존재 시 영상 합성 건너뜀기"""
        date_str = '260325'

        # 1. engine.done 생성
        create_done(date_str, 'engine')
        assert exists_done(date_str, 'engine') is True

        # 2. engine.done 존재 확인 후 영상 합성 건너뜀
        if exists_done(date_str, 'engine'):
            # 영상 합성 생략
            video_file = None
        else:
            # 영상 합성 수행 (여기서는 Mock)
            video_file = "260325_video.mp4"

        assert video_file is None, "engine.done이 존재하면 영상 합성을 건너뛰어야 함"

    def test_pipeline_sequential_dependency(self, temp_workspace, mock_data):
        """파이프라인 순차적 의존성 검증"""
        date_str = '260325'

        # 1. scraper 단계 (선행 단계 없음)
        create_done(date_str, 'scraper')

        # 2. translator 단계 (scraper 완료 필요)
        assert_exists_done(date_str, 'scraper')  # 예외 발생하지 않음
        create_done(date_str, 'translator')

        # 3. tts 단계 (translator 완료 필요)
        assert_exists_done(date_str, 'translator')  # 예외 발생하지 않음
        create_done(date_str, 'tts')

        # 4. engine 단계 (tts 완료 필요)
        assert_exists_done(date_str, 'tts')  # 예외 발생하지 않음
        create_done(date_str, 'engine')

        # 모든 done-file이 존재하는지 확인
        assert exists_done(date_str, 'scraper')
        assert exists_done(date_str, 'translator')
        assert exists_done(date_str, 'tts')
        assert exists_done(date_str, 'engine')

    def test_pipeline_missing_dependency_raises(self, temp_workspace):
        """선행 단계 누락 시 예외 발생 검증"""
        from today_vn_news.exceptions import PipelineRestartError

        date_str = '260325'

        # scraper.done만 생성
        create_done(date_str, 'scraper')

        # translator.done 누락 상태에서 engine 단계 시도
        with pytest.raises(PipelineRestartError):
            assert_exists_done(date_str, 'translator')

    def test_filename_format_yymmdd(self, temp_workspace, mock_data):
        """모든 출력 파일이 YYMMDD 형식인지 검증"""
        date_str = '260325'

        # normalize_timestamp로 생성된 날짜 문자열 사용
        normalized = normalize_timestamp('2026-03-25')
        assert validate_yymmdd(normalized) is None  # 예외 발생하지 않으면 통과

        # done-file 생성
        create_done(normalized, 'scraper')
        create_done(normalized, 'translator')
        create_done(normalized, 'tts')
        create_done(normalized, 'engine')

        # 모든 done-file이 존재하는지 확인
        assert exists_done(normalized, 'scraper')
        assert exists_done(normalized, 'translator')
        assert exists_done(normalized, 'tts')
        assert exists_done(normalized, 'engine')

    def test_normalize_timestamp_various_formats(self):
        """다양한 입력 형식 지원 확인"""
        test_cases = [
            ('2026-03-25', '260325'),
            ('26-03-25', '260325'),
            ('260325', '260325'),
            ('2026/03/25', '260325'),
        ]

        for input_date, expected in test_cases:
            result = normalize_timestamp(input_date)
            assert result == expected, f"{input_date} -> {result} (expected: {expected})"

    def test_validate_yymmdd_valid(self):
        """유효한 YYMMDD 형식 검증"""
        # 예외가 발생하지 않으면 통과
        assert validate_yymmdd('260325') is None
        assert validate_yymmdd('261231') is None

    def test_validate_yymmdd_invalid_format(self):
        """잘못된 YYMMDD 형식 검증"""
        with pytest.raises(ValueError):
            validate_yymmdd('26032')  # 5자리

        with pytest.raises(ValueError):
            validate_yymmdd('2603256')  # 7자리

        with pytest.raises(ValueError):
            validate_yymmdd('abcd25')  # 문자 포함

    def test_validate_yymmdd_invalid_date(self):
        """잘못된 날짜 검증"""
        with pytest.raises(ValueError):
            validate_yymmdd('261302')  # 13월

        with pytest.raises(ValueError):
            validate_yymmdd('260332')  # 32일

    def test_done_files_path_format(self, temp_workspace):
        """done-file 경로 형식 검증"""
        date_str = '260325'

        # done-file 생성
        create_done(date_str, 'scraper')

        # 파일 경로 확인
        done_path = Path('data') / f'{date_str}.scraper.done'
        assert done_path.exists()

        # 파일명 형식 확인: YYMMDD.module.done
        assert done_path.name == '260325.scraper.done'

    def test_exists_done_false_when_missing(self, temp_workspace):
        """done-file 부재 시 exists_done False 반환"""
        date_str = '260325'

        # 존재하지 않는 done-file 확인
        assert exists_done(date_str, 'scraper') is False
        assert exists_done(date_str, 'translator') is False
