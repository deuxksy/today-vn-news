# tests/unit/test_notifications/test_pushover.py
import os
import pytest
from unittest.mock import Mock, patch
from today_vn_news.notifications.pushover import PushoverNotifier
from today_vn_news.notifications import PipelineStatus, STEP_SCRAPE


class TestPushoverNotifierCreation:
    """PushoverNotifier 인스턴스 생성 테스트"""

    def test_from_env_or_none_returns_none_when_missing(self, monkeypatch):
        """환경 변수 없으면 None 반환"""
        monkeypatch.delenv("PUSHOVER_TOKEN", raising=False)
        monkeypatch.delenv("PUSHOVER_USER", raising=False)

        result = PushoverNotifier.from_env_or_none()
        assert result is None

    def test_from_env_or_none_returns_instance_when_set(self, monkeypatch):
        """환경 변수 있으면 인스턴스 반환"""
        monkeypatch.setenv("PUSHOVER_TOKEN", "test_token_123456789012345678")
        monkeypatch.setenv("PUSHOVER_USER", "test_user_123456789012345678")

        result = PushoverNotifier.from_env_or_none()
        assert result is not None
        assert result.token == "test_token_123456789012345678"
        assert result.user == "test_user_123456789012345678"

    def test_from_env_raises_when_missing(self, monkeypatch):
        """from_env는 환경 변수 없으면 ValueError"""
        monkeypatch.delenv("PUSHOVER_TOKEN", raising=False)
        monkeypatch.delenv("PUSHOVER_USER", raising=False)

        with pytest.raises(ValueError, match="PUSHOVER_TOKEN and PUSHOVER_USER required"):
            PushoverNotifier.from_env()


class TestPushoverNotifierSend:
    """PushoverNotifier.send_notification 테스트"""

    def test_send_notification_success(self, monkeypatch):
        """API 성공 시 True 반환"""
        monkeypatch.setenv("PUSHOVER_TOKEN", "test_token")
        monkeypatch.setenv("PUSHOVER_USER", "test_user")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 1}

        with patch("requests.post", return_value=mock_response) as mock_post:
            notifier = PushoverNotifier.from_env()
            status = PipelineStatus()
            status.steps[STEP_SCRAPE] = True

            result = notifier.send_notification(status)

            assert result is True
            mock_post.assert_called_once()
            # API 호출 파라미터 검증
            call_data = mock_post.call_args[1]["data"]
            assert call_data["token"] == "test_token"
            assert call_data["user"] == "test_user"

    def test_send_notification_rate_limit_returns_false(self, monkeypatch):
        """HTTP 429 Rate Limit 시 False 반환"""
        monkeypatch.setenv("PUSHOVER_TOKEN", "test_token")
        monkeypatch.setenv("PUSHOVER_USER", "test_user")

        mock_response = Mock()
        mock_response.status_code = 429

        with patch("requests.post", return_value=mock_response):
            notifier = PushoverNotifier.from_env()
            status = PipelineStatus()

            result = notifier.send_notification(status)
            assert result is False

    def test_send_notification_api_error_returns_false(self, monkeypatch):
        """API 에러 시 False 반환 (예외 없음)"""
        monkeypatch.setenv("PUSHOVER_TOKEN", "test_token")
        monkeypatch.setenv("PUSHOVER_USER", "test_user")

        with patch("requests.post", side_effect=Exception("Network error")):
            notifier = PushoverNotifier.from_env()
            status = PipelineStatus()

            result = notifier.send_notification(status)
            assert result is False

    def test_send_notification_emergency_includes_retry_expire(self, monkeypatch):
        """Emergency priority(2) 시 retry, expire 파라미터 포함"""
        monkeypatch.setenv("PUSHOVER_TOKEN", "test_token")
        monkeypatch.setenv("PUSHOVER_USER", "test_user")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 1}

        with patch("requests.post", return_value=mock_response) as mock_post:
            notifier = PushoverNotifier.from_env()
            status = PipelineStatus()
            status.errors[STEP_SCRAPE] = "Network error"  # 전체 실패 = Emergency

            result = notifier.send_notification(status)

            call_data = mock_post.call_args[1]["data"]
            assert call_data["priority"] == 2
            assert call_data["retry"] == 300
            assert call_data["expire"] == 3600
