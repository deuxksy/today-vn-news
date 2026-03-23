# tests/unit/test_notifications/test_pipeline_status.py
import pytest
from today_vn_news.notifications import PipelineStatus, STEP_SCRAPE, STEP_TRANSLATE


class TestPipelineStatusSuccess:
    """PipelineStatus.success 프로퍼티 테스트"""

    def test_empty_steps_returns_false(self):
        """빈 steps 딕셔너리일 때 success는 False"""
        status = PipelineStatus()
        assert status.success is False

    def test_all_steps_true_no_errors_returns_true(self):
        """모든 단계 성공, 에러 없으면 success는 True"""
        status = PipelineStatus()
        status.steps[STEP_SCRAPE] = True
        status.steps[STEP_TRANSLATE] = True
        assert status.success is True

    def test_partial_success_with_error_returns_false(self):
        """일부 성공이어도 에러 있으면 success는 False"""
        status = PipelineStatus()
        status.steps[STEP_SCRAPE] = True
        status.errors[STEP_TRANSLATE] = "API error"
        assert status.success is False

    def test_all_steps_true_with_error_returns_false(self):
        """모든 단계 성공해도 에러 있으면 success는 False"""
        status = PipelineStatus()
        status.steps[STEP_SCRAPE] = True
        status.steps[STEP_TRANSLATE] = True
        status.errors["upload"] = "Quota exceeded"
        assert status.success is False


class TestPipelineStatusFailedStep:
    """PipelineStatus.failed_step 프로퍼티 테스트"""

    def test_no_failure_returns_none(self):
        """실패 없으면 None 반환"""
        status = PipelineStatus()
        status.steps[STEP_SCRAPE] = True
        assert status.failed_step is None

    def test_first_failed_step_returned(self):
        """첫 번째 실패 단계 반환"""
        status = PipelineStatus()
        status.steps[STEP_SCRAPE] = True
        status.errors[STEP_TRANSLATE] = "API error"
        assert status.failed_step == STEP_TRANSLATE

    def test_completed_steps_empty_on_all_fail(self):
        """전체 실패 시 completed_steps는 빈 리스트"""
        status = PipelineStatus()
        status.errors[STEP_SCRAPE] = "Network error"
        assert status.completed_steps == []
