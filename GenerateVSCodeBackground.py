import argparse
import os
import subprocess
import re
import datetime
from typing import Literal, cast
import cv2
from skimage.metrics import structural_similarity as ssim


def run(
    reuse_local,
    boomerang,
    perfect_loop,
    duration,
    start_time,
    output_name,
    quality: Literal["low", "high", "immaculate"],
):
    temp_video_name = "temp.mp4"
    should_download = not reuse_local

    cleaned_url = None
    youtube_url = None

    if should_download:
        youtube_url = input("Enter YouTube URL: ")
        # remove everything after '?' or '&' as long as it isn't ?v=
        cleaned_url = re.split(r"\?[^v]|&", youtube_url)[0]
        if youtube_url != cleaned_url:
            print(f"Cleaned the URL, set to: {cleaned_url}\n")

    if start_time is None:
        start_time = input("Enter start time (HH:MM:SS or MM:SS or specify in seconds, default=0): ") or "0"

    if not boomerang and not perfect_loop and duration is None:
        duration = input(
            "Enter duration to capture (in seconds, required if not using --boomerang or --perfect-loop): "
        )
        if not duration:
            print("Duration is required when not using perfect loop or boomerang mode.")
            return

    if output_name is None:
        output_name = input("Enter output file name (without extension, default=output.webp): ") or "output"

    is_perfect_loop_mode = perfect_loop
    if is_perfect_loop_mode:
        # Default to 30s if nothing else found
        duration = 30

    try:

        def convert_to_seconds(time_str) -> int:
            time_parts = time_str.split(":")
            if len(time_parts) == 3:
                hours, minutes, seconds = map(int, time_parts)
                total_seconds = hours * 3600 + minutes * 60 + seconds
            elif len(time_parts) == 2:
                minutes, seconds = map(int, time_parts)
                total_seconds = minutes * 60 + seconds
            else:
                total_seconds = int(time_str)
            return total_seconds

        def convert_to_hhmmss(total_seconds):
            return str(datetime.timedelta(seconds=total_seconds))

        # Convert times to seconds
        start_seconds = convert_to_seconds(start_time)
        # For perfect loop, duration is dummy (will be replaced later)
        if duration is not None:
            duration_seconds = int(duration)
        else:
            duration_seconds = None

        # Calculate end time in seconds
        if duration_seconds is not None:
            end_time_seconds = start_seconds + duration_seconds
            end_time = convert_to_hhmmss(end_time_seconds)
            print(f"Start time is {start_time} (in seconds: {start_seconds}), duration is {duration_seconds} seconds.")
            print(f"End time calculated to be {end_time} (in seconds: {end_time_seconds}).")
        else:
            print(f"Start time is {start_time} (in seconds: {start_seconds}), duration: perfect loop/boomerang mode.")

        if should_download:
            yt_dlp_command = [
                "yt-dlp",
                "-f",
                "bestvideo[height<=1080]",
                "-o",
                temp_video_name,
                cleaned_url,
            ]
            print("Fetching video URL...")
            subprocess.run(yt_dlp_command, check=True)

        trimmed_video_name = "temp_trimmed.mp4"
        # For boomerang or perfect loop use a provisional duration (will be clipped after detection)
        if duration_seconds is None:
            ffmpeg_duration = 60  # up to 60s, for detection
        else:
            ffmpeg_duration = duration_seconds

        ffmpeg_trim_cmd = [
            "ffmpeg",
            "-ss",
            str(start_seconds),
            "-i",
            temp_video_name,
            "-t",
            str(ffmpeg_duration),
            "-c:v",
            "libx264",
            "-y",
            trimmed_video_name,
        ]
        subprocess.run(ffmpeg_trim_cmd, check=True)

        # Boomerang mode (to implement later)
        if boomerang:
            print("Boomerang mode currently not implemented.")
            # Placeholder to call boomerang logic
            # convert_to_boomerang(...)
            return

        # Perfect loop mode
        if is_perfect_loop_mode:
            try:
                detected_duration = detect_perfect_loop_v2(trimmed_video_name)
                print(f"Perfect Loop found: Using {detected_duration:.2f} seconds as loop length")
                duration_seconds = int(detected_duration)
            except Exception:
                print(
                    f"Perfect loop wasn't found. Giving up and using {ffmpeg_duration}s for this run. If you want to retry, pick a different start time."
                )
                duration_seconds = ffmpeg_duration

        # Step 3: Create WebP using ffmpeg
        output_and_extension = f"{output_name}.webp"
        webp_command = [
            "ffmpeg",
            "-i",
            trimmed_video_name,
            "-an",
        ]
        if duration_seconds is not None:
            webp_command += ["-t", str(duration_seconds)]

        # Apply quality options
        if quality == "immaculate":
            webp_command += [
                "-lossless",
                "1",
                "-quality",
                "100",
            ]
            target_fps = 30
        elif quality == "high":
            webp_command += [
                "-lossless",
                "0",
                "-quality",
                "100",
            ]
            target_fps = 24
        else:  # low
            webp_command += [
                "-lossless",
                "0",
                "-quality",
                "90",
            ]
            target_fps = 15

        # Update fps in the filter
        webp_command += [
            "-vf",
            f"fps={target_fps},scale=1920:-1:flags=lanczos",
        ]

        webp_command += [
            "-c:v",
            "libwebp_anim",
            "-loop",
            "0",
            "-y",
            output_and_extension,
        ]

        print("Running ffmpeg command: ", " ".join(webp_command))
        webp_run = subprocess.run(webp_command)

        if webp_run.returncode == 0:
            print(f"{quality}-quality WebP saved as {output_and_extension}")
        else:
            print("Failed to create WebP.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred. Ensure yt-dlp is up to date. Here is what failed: {e}")
        if "output_and_extension" in locals() and os.path.exists(output_and_extension):
            os.remove(output_and_extension)
    finally:
        if os.path.exists(trimmed_video_name):
            os.remove(trimmed_video_name)
        # By default, do NOT delete temp.mp4 anymore


def convert_to_boomerang():
    pass


def detect_perfect_loop_v2(
    video_path: str,
    min_duration_seconds: float = 3,
    max_duration_seconds: float = 60,
    verify_window_seconds: float = 0.5,
    downscale: tuple[int, int] = (320, 180),
    ssim_threshold: float = 0.982,
) -> float:
    """

    Notes on ssim_threshold experimentation:
    - 0.990 worked for snowflake background (challenging)
    - 0.980 worked too for background with animated snowflakes, but I think I noticed a tiny stutter. Barely noticeable unless you stare hard at your background
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("Cannot open video")

    fps = cap.get(cv2.CAP_PROP_FPS)

    ok, first = cap.read()
    if not ok:
        raise RuntimeError("Cannot read first frame")

    first = cv2.cvtColor(first, cv2.COLOR_BGR2GRAY)
    first = cv2.resize(first, downscale)

    frames = [first]
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.resize(frame, downscale)
        frames.append(frame)

    cap.release()

    min_offset = int(min_duration_seconds * fps)
    max_offset = min(int(max_duration_seconds * fps), len(frames) - 1)

    best_offset = None
    for offset in range(max_offset, min_offset - 1, -1):
        score: float = ssim(frames[0], frames[offset], data_range=255, full=False)
        if score < ssim_threshold:
            continue

        verify_frames = int(verify_window_seconds * fps)
        success = True
        for k in range(1, verify_frames + 1):
            if offset + k >= len(frames):
                success = False
                break
            score = ssim(frames[k], frames[offset + k], data_range=255, full=False)
            if score < ssim_threshold:
                success = False
                break

        if success:
            best_offset = offset
            break

    if best_offset is None:
        raise RuntimeError("Perfect loop not found")

    return best_offset / fps


def get_fps(video_path) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "0",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=r_frame_rate",
        "-of",
        "csv=p=0",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    fps: float = eval(result.stdout.strip())
    return round(fps, 2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate animated VSCode backgrounds from YouTube. Can detect perfect loops and supports boomerang animations."
    )
    parser.add_argument(
        "-r",
        "--reuse-local",
        action="store_true",
        help="Reuse the last downloaded video (saved as temp.mp4) and skip downloading the video. Useful for quickly retrying with different settings.",
    )
    parser.add_argument(
        "-b",
        "--boomerang",
        action="store_true",
        help="Use boomerang/rewind mode instead of perfect loop. Great if you can't find a perfect loop.",
    )
    parser.add_argument(
        "-p", "--perfect-loop", action="store_true", help="Detect perfect loop automatically from the clip."
    )
    parser.add_argument(
        "-d",
        "--duration",
        type=str,
        default=15,
        help="Duration of clip in seconds (required if not using --perfect-loop). Default is 15 seconds. It is not recommended to go much past 30 seconds.",
    )
    parser.add_argument(
        "-s",
        "--start-time",
        type=str,
        default="0",
        help="Start time, you can provide in HH:MM:SS or MM:SS or just seconds. (default: 0)",
    )
    parser.add_argument(
        "-o",
        "--output-name",
        type=str,
        default="output",
        help="Choose output file name without extension. (default: output)",
    )
    parser.add_argument(
        "-q",
        "--quality",
        choices=["low", "high", "immaculate"],
        default="high",
        help="Set output quality: low (fast, ugly), high (recommended), or immaculate (max possible, slowest & resource expensive). Default is high. If high still doesn't look good then try immaculate.",
    )

    args = parser.parse_args()

    if cast(str, args.output_name).endswith(".webp"):
        args.output_name = args.output_name[:-5]

    if args.perfect_loop:
        args.duration = "30"

    run(
        reuse_local=args.reuse_local,
        boomerang=args.boomerang,
        perfect_loop=args.perfect_loop,
        duration=args.duration,
        start_time=args.start_time,
        output_name=args.output_name,
        quality=args.quality,
    )
