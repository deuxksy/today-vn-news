# today_vn_news/notifications/pipeline_status.py
from dataclasses import dataclass, field
from typing import Optional

# 단계 키 상수
STEP_SCRAPE = "scrape"
STEP_TRANSLATE = "translate"
STEP_TTS = "tts"
STEP_VIDEO = "video"
STEP_UPLOAD = "upload"
STEP_ARCHIVE = "archive"

ALL_STEPS = [STEP_SCRAPE, STEP_TRANSLATE, STEP_TTS, STEP_VIDEO, STEP_UPLOAD, STEP_ARCHIVE]


@dataclass
class PipelineStatus:
    """파이프라인 실행 상태 추적

    steps 딕셔너리 키 규칙:
    - "scrape": 뉴스 수집 단계
    - "translate": 번역 단계
    - "tts": TTS 음성 생성 단계
    - "video": 영상 합성 단계
    - "upload": YouTube 업로드 단계
    - "archive": Media 저장 단계
    """
    steps: dict[str, bool] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)
    youtube_url: Optional[str] = None

    @property
    def success(self) -> bool:
        """전체 성공 여부 (빈 steps 딕셔너리는 실패로 처리)"""
        return bool(self.steps) and all(self.steps.values()) and not self.errors

    @property
    def failed_step(self) -> Optional[str]:
        """첫 번째 실패 단계 반환"""
        for step in ALL_STEPS:
            if step in self.steps and not self.steps[step]:
                return step
            if step in self.errors:
                return step
        return None

    @property
    def completed_steps(self) -> list[str]:
        """성공한 단계 목록 (순서 보장)"""
        return [step for step in ALL_STEPS if self.steps.get(step, False)]
