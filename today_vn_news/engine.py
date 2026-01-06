#!/usr/bin/env python3
import subprocess
import os
import sys

"""
영상 합성 엔진 (FFmpeg Wrapper)
- 목적: 정제된 음성(MP3)과 배경 영상(MOV)을 합쳐 최종 뉴스 영상 생성
- 상세 사양: ContextFile.md 3.1, 47절 및 6절 참조
- 업데이트: 영상 오디오 제거, TTS 길이에 맞춰 영상 루프/컷 처리
"""

def get_hw_encoder():
    """
    현재 시스템 환경에 맞는 하드웨어 가속 인코더 반환
    """
    if sys.platform == "darwin":
        return "h264_videotoolbox"
    
    try:
        res = subprocess.run(["ffmpeg", "-encoders"], capture_output=True, text=True)
        if "h264_vaapi" in res.stdout:
            return "h264_vaapi"
    except:
        pass
        
    return "libx264"

def synthesize_video(base_name: str, data_dir: str = "data"):
    """
    영상과 음성을 합성하여 최종 MP4 생성
    - 원본 영상의 소리는 제거하고 TTS 음성만 삽입
    - 영상의 길이를 TTS 음성 길이에 정확히 맞춤 (부족하면 루프, 길면 컷)
    """
    video_in = os.path.join(data_dir, f"{base_name}.mov")
    audio_in = os.path.join(data_dir, f"{base_name}.mp3")
    video_out = os.path.join(data_dir, f"{base_name}_final.mp4")

    if not os.path.exists(video_in) or not os.path.exists(audio_in):
        print(f"[!] 필수 입력 파일이 없습니다. (Video: {os.path.exists(video_in)}, Audio: {os.path.exists(audio_in)})")
        return False

    encoder = get_hw_encoder()
    print(f"[*] 영상 합성 시작: {base_name}")
    print(f"[*] 사용 인코더: {encoder}")
    print("[*] 오디오 제거 및 TTS 길이 맞춤 설정 적용 중...")

    # FFmpeg 명령어 구성
    # -stream_loop -1: 영상이 오디오보다 짧을 경우 무한 루프
    # -i video_in: 영상 입력
    # -i audio_in: 음성 입력
    # -map 0:v:0: 첫 번째 입력(영상)의 비디오만 사용 (원본 소리 제거)
    # -map 1:a:0: 두 번째 입력(음성)의 오디오만 사용
    # -shortest: 입력 중 가장 짧은 스트림(여기서는 오디오)이 끝나면 종료
    # -fflags +genpts: 루프 시 타임스탬프 재생성
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",    # 영상 무한 루프 설정
        "-i", video_in,
        "-i", audio_in,
        "-map", "0:v:0",         # 비디오만 맵핑 (오디오 제거 효과)
        "-map", "1:a:0",         # TTS 오디오 맵핑
        "-c:v", encoder,
        "-b:v", "5000k",
        "-c:a", "aac",
        "-shortest",             # TTS 오디오 길이에 맞춰 중단
        "-fflags", "+genpts",    # 루프 시 안정적인 타임스탬프 생성
        video_out
    ]

    try:
        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode == 0:
            print(f"[+] 최종 영상 생성 완료: {video_out}")
            return True
        else:
            print(f"[!] FFmpeg 실행 에러:")
            print(process.stderr)
            return False
    except Exception as e:
        print(f"[!] 예기치 못한 오류: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        synthesize_video(sys.argv[1])
    else:
        synthesize_video("260106")
