#!/usr/bin/env python3
import subprocess
import os
import sys

from today_vn_news.logger import logger
from today_vn_news.exceptions import VideoSynthesisError

"""
영상 합성 엔진 (FFmpeg Wrapper)
- 목적: 정제된 음성(MP3)과 배경 영상(MOV)을 합쳐 최종 뉴스 영상 생성
- 상세 사양: ContextFile.md 3.1 (인프라) 및 3.2 (기술 스택) 참조
- 업데이트: 영상 오디오 제거, TTS 길이에 맞춰 영상 루프/컷 처리
"""

def get_hw_encoder_config():
    """
    현재 시스템 환경에 맞는 하드웨어 가속 인코더 및 옵션 반환
    Returns: (encoder_name, extra_input_flags, extra_output_flags)
    """
    if sys.platform == "darwin":
        return "h264_videotoolbox", [], []
    
    # Linux (VAAPI check)
    try:
        # Check for renderD128 (common DRI render node)
        if os.path.exists("/dev/dri/renderD128"):
            res = subprocess.run(["ffmpeg", "-encoders"], capture_output=True, text=True)
            if "h264_vaapi" in res.stdout:
                # Steam Deck / Standard Linux VAAPI
                # Input args: -vaapi_device /dev/dri/renderD128
                # Output args: -vf format=nv12,hwupload
                return "h264_vaapi", ["-vaapi_device", "/dev/dri/renderD128"], ["-vf", "format=nv12,hwupload"]
    except:
        pass
        
    return "libx264", [], []

def synthesize_video(base_name: str, data_dir: str = "data"):
    """
    영상과 음성을 합성하여 최종 MP4 생성
    - 원본 영상의 소리는 제거하고 TTS 음성만 삽입
    - 영상의 길이를 TTS 음성 길이에 정확히 맞춤 (부족하면 루프, 길면 컷)
    """
    video_mov = os.path.join(data_dir, f"{base_name}.mov")
    video_mp4 = os.path.join(data_dir, f"{base_name}.mp4")
    audio_in = os.path.join(data_dir, f"{base_name}.mp3")
    video_out = os.path.join(data_dir, f"{base_name}_final.mp4")

    # MOV 또는 MP4 중 존재하는 파일 선택
    video_in = video_mov if os.path.exists(video_mov) else video_mp4
    
    # 기본 이미지 경로
    default_img = "assets/default_bg.png"
    using_image = False

    if not os.path.exists(video_in):
        if os.path.exists(default_img):
            logger.info(f"영상을 찾을 수 없어 기본 이미지({default_img})를 사용합니다.")
            video_in = default_img
            using_image = True
        else:
            logger.error(f"영상이나 기본 이미지({default_img})가 없습니다. 합성이 불가능합니다.")
            raise VideoSynthesisError(f"영상이나 기본 이미지({default_img})가 없습니다.")

    if not os.path.exists(audio_in):
        logger.error(f"필수 오디오 파일이 없습니다: {audio_in}")
        raise VideoSynthesisError(f"필수 오디오 파일이 없습니다: {audio_in}")

    encoder, input_flags, output_flags = get_hw_encoder_config()
    logger.info(f"영상 합성 시작: {base_name}")
    logger.info(f"사용 인코더: {encoder}")
    if input_flags:
        logger.info(f"가속 옵션: {' '.join(input_flags)} {' '.join(output_flags)}")
    
    # FFmpeg 명령어 구성
    cmd = ["ffmpeg", "-y"]
    cmd.extend(input_flags)
    
    if using_image:
        # 이미지일 경우: 1프레임 이미지를 무한 루프
        cmd.extend(["-loop", "1", "-i", video_in])
    else:
        # 영상일 경우: 루프 설정
        cmd.extend(["-stream_loop", "-1", "-i", video_in])
        
    cmd.extend([
        "-i", audio_in,
        "-map", "0:v:0",         # 비디오(또는 루프되는 이미지)
        "-map", "1:a:0",         # TTS 오디오
        "-c:v", encoder
    ])
    
    # 이미지일 경우 추가적인 비디오 필터 (픽셀 포맷 보정 등)
    if using_image:
        # yuv420p는 대부분의 플레이어 및 유튜브 호환성을 위함
        cmd.extend(["-pix_fmt", "yuv420p", "-r", "30"])
    
    cmd.extend(output_flags)
    
    cmd.extend([
        "-b:v", "5000k",
        "-c:a", "aac",
        "-shortest",             # TTS 오디오 길이에 맞춰 중단
        "-fflags", "+genpts",    # 루프 시 안정적인 타임스탬프 생성
        video_out
    ])

    try:
        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode == 0:
            logger.info(f"최종 영상 생성 완료: {video_out}")
            return True
        else:
            logger.error("FFmpeg 실행 에러:")
            # stderr 전체를 출력 (긴 로그도 잘리지 않음)
            if process.stderr:
                logger.error(process.stderr)
            # stdout도 있으면 출력
            if process.stdout:
                logger.error(f"FFmpeg stdout: {process.stdout}")
            raise VideoSynthesisError("FFmpeg 실행 실패")
    except FileNotFoundError:
        logger.error("FFmpeg가 설치되지 않았습니다.")
        raise VideoSynthesisError("FFmpeg가 설치되지 않았습니다.")
    except VideoSynthesisError:
        raise
    except Exception as e:
        logger.error(f"예기치 못한 오류: {str(e)}")
        raise VideoSynthesisError(f"예기치 못한 오류: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        synthesize_video(sys.argv[1])
    else:
        synthesize_video("260106")
