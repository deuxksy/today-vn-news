"""Pushover 알림 통합 테스트 (Mock API)

실제 Pushover API는 호출하지 않고 mock을 사용하여 알림 로직을 검증합니다.
"""
import pytest
from unittest.mock import Mock, patch
from today_vn_news.notifications.pipeline_status import (
    PipelineStatus,
    STEP_SCRAPE,
    STEP_TRANSLATE,
    STEP_TTS,
    STEP_VIDEO,
    STEP_UPLOAD,
    STEP_ARCHIVE,
    ALL_STEPS,
)
from today_vn_news.notifications.pushover import PushoverNotifier


@pytest.fixture
def mock_pipeline_status_success():
    """전체 성공 상태 mock"""
    status = PipelineStatus()
    for step in ALL_STEPS:
        status.steps[step] = True
    status.youtube_url = "https://youtu.be/dQw4w9WgXcQ"
    return status


@pytest.fixture
def mock_pipeline_status_partial_failure():
    """부분 실패 상태 mock"""
    status = PipelineStatus()
    status.steps[STEP_SCRAPE] = True
    status.steps[STEP_TRANSLATE] = True
    status.steps[STEP_TTS] = True
    status.steps[STEP_VIDEO] = True
    status.errors[STEP_UPLOAD] = "API quota exceeded"
    return status


@pytest.fixture
def mock_pipeline_status_total_failure():
    """전체 실패 상태 mock"""
    status = PipelineStatus()
    status.errors[STEP_SCRAPE] = "Network error"
    return status


class TestPushoverIntegration:
    """Pushover 알림 통합 테스트"""

    @patch("today_vn_news.notifications.pushover.requests.post")
    def test_notification_success_all_steps(self, mock_post, mock_pipeline_status_success):
        """전체 성공 시 알림 검증"""
        # Mock API 응답
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 1}
        mock_post.return_value = mock_response

        # Notifier 생성 (가� 토큰/유저)
        notifier = PushoverNotifier("test_token", "test_user")

        # 알림 전송
        result = notifier.send_notification(mock_pipeline_status_success)

        # 검증
        assert result is True
        mock_post.assert_called_once()

        # API 호출 파라미터 검증
        call_args = mock_post.call_args
        data = call_args.kwargs.get("data") or call_args[1].get("data")

        assert data["token"] == "test_token"
        assert data["user"] == "test_user"
        assert data["title"] == "✅ 뉴스 영상 완료"
        assert "완료 단계:" in data["message"]
        assert data["priority"] == 0  # Normal
        assert data["url"] == "https://youtu.be/dQw4w9WgXcQ"
        assert "retry" not in data  # Normal priority는 retry/expire 없음

    @patch("today_vn_news.notifications.pushover.requests.post")
    def test_notification_partial_failure(self, mock_post, mock_pipeline_status_partial_failure):
        """부분 실패 시 알림 검증"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 1}
        mock_post.return_value = mock_response

        notifier = PushoverNotifier("test_token", "test_user")
        result = notifier.send_notification(mock_pipeline_status_partial_failure)

        assert result is True
        call_args = mock_post.call_args
        data = call_args.kwargs.get("data") or call_args[1].get("data")

        assert data["title"] == "⚠️ 파이프라인 부분 실패"
        assert "성공:" in data["message"]
        assert "실패:" in data["message"]
        assert "upload - API quota exceeded" in data["message"]
        assert data["priority"] == 1  # High
        assert "url" not in data  # 부분 실패는 URL 없음

    @patch("today_vn_news.notifications.pushover.requests.post")
    def test_notification_total_failure_emergency(self, mock_post, mock_pipeline_status_total_failure):
        """전체 실패 시 Emergency priority 알림 검증"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 1}
        mock_post.return_value = mock_response

        notifier = PushoverNotifier("test_token", "test_user")
        result = notifier.send_notification(mock_pipeline_status_total_failure)

        assert result is True
        call_args = mock_post.call_args
        data = call_args.kwargs.get("data") or call_args[1].get("data")

        assert data["title"] == "❌ 파이프라인 실패"
        assert "사유: Network error" in data["message"]
        assert data["priority"] == 2  # Emergency
        assert data["retry"] == 300  # 5분마다 재시도
        assert data["expire"] == 3600  # 1시간 후 만료
        assert "url" not in data

    @patch("today_vn_news.notifications.pushover.requests.post")
    def test_notification_rate_limit_handling(self, mock_post, mock_pipeline_status_success):
        """Rate Limit (HTTP 429) 처리 검증"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_post.return_value = mock_response

        notifier = PushoverNotifier("test_token", "test_user")
        result = notifier.send_notification(mock_pipeline_status_success)

        assert result is False  # 실패 반환
        mock_post.assert_called_once()

    @patch("today_vn_news.notifications.pushover.requests.post")
    def test_notification_api_error_handling(self, mock_post, mock_pipeline_status_success):
        """API 에러 (500) 처리 검증"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        notifier = PushoverNotifier("test_token", "test_user")
        result = notifier.send_notification(mock_pipeline_status_success)

        assert result is False  # 실패 반환

    @patch("today_vn_news.notifications.pushover.requests.post")
    def test_notification_network_error_handling(self, mock_post, mock_pipeline_status_success):
        """네트워크 에러 처리 검증"""
        mock_post.side_effect = Exception("Connection timeout")

        notifier = PushoverNotifier("test_token", "test_user")
        result = notifier.send_notification(mock_pipeline_status_success)

        assert result is False  # 실패 반환

    @patch("today_vn_news.notifications.pushover.requests.post")
    def test_message_truncation(self, mock_post, mock_pipeline_status_success):
        """메시지 길이 제한 초과 시 자르기 검증"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 1}
        mock_post.return_value = mock_response

        # 매우 긴 메시지 생성
        status = PipelineStatus()
        for step in ALL_STEPS:
            status.steps[step] = True
        # 긴 YouTube URL (512자 초과)
        status.youtube_url = "https://youtu.be/" + "a" * 600

        notifier = PushoverNotifier("test_token", "test_user")
        result = notifier.send_notification(status)

        assert result is True
        call_args = mock_post.call_args
        data = call_args.kwargs.get("data") or call_args[1].get("data")

        # URL이 512자로 잘렸는지 확인
        assert len(data["url"]) <= 512
        # prefix(17) + padding(495) = 512
        assert data["url"] == "https://youtu.be/" + "a" * 495

    @patch("today_vn_news.notifications.pushover.requests.post")
    def test_from_env_or_none_without_env(self, mock_post):
        """환경 변수 없을 때 None 반환 검증"""
        with patch.dict("os.environ", {}, clear=True):
            notifier = PushoverNotifier.from_env_or_none()
            assert notifier is None

    @patch("today_vn_news.notifications.pushover.requests.post")
    def test_from_env_or_none_with_env(self, mock_post):
        """환경 변수 있을 때 인스턴스 반환 검증"""
        env_vars = {
            "PUSHOVER_TOKEN": "test_token",
            "PUSHOVER_USER": "test_user",
        }
        with patch.dict("os.environ", env_vars, clear=True):
            notifier = PushoverNotifier.from_env_or_none()
            assert notifier is not None
            assert notifier.token == "test_token"
            assert notifier.user == "test_user"

    def test_all_steps_constant_order(self):
        """ALL_STEPS 상수 순서 검증"""
        expected_order = [
            STEP_SCRAPE,
            STEP_TRANSLATE,
            STEP_TTS,
            STEP_VIDEO,
            STEP_UPLOAD,
            STEP_ARCHIVE,
        ]
        assert ALL_STEPS == expected_order
