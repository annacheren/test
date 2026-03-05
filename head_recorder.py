"""
RGBD Head Movement Recorder — Luxonis OAK-D Pro
================================================
Records 5 sessions of synchronized color + depth (RGBD) video.
Each session is max 15 seconds, manually triggered by ENTER.

Flow per session:
  1. Popup: "Ready for session X — press ENTER to start"
  2. ENTER pressed → recording starts
  3. 15 seconds → auto-stops → popup: "Session X done — press ENTER for next"
  4. ENTER pressed → next session
  5. After session 5 → popup: "All done!"

Controls:
  ENTER  →  confirm popup / start next session
  Q      →  quit at any time

Requirements:
  pip install depthai opencv-python numpy

Usage:
  python head_recorder.py
  python head_recorder.py --output-dir ./my_recordings --sessions 5
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import depthai as dai

# ── CLI ───────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--output-dir", default="recordings")
parser.add_argument("--sessions",   type=int,   default=5)
parser.add_argument("--duration",   type=float, default=15.0)
parser.add_argument("--fps",        type=int,   default=15)
args = parser.parse_args()

OUTPUT_DIR   = Path(args.output_dir)
TOTAL        = args.sessions
MAX_DURATION = args.duration
FPS          = args.fps
PREVIEW_W    = 1280
PREVIEW_H    = 720

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Colors (BGR) ──────────────────────────────────────────────────────────────
GREEN        = (80,  220, 100)
RED          = (60,  80,  240)
AMBER        = (40,  180, 240)
WHITE        = (235, 235, 235)
GRAY         = (100, 100, 100)
BG           = (25,  25,  35)
POPUP_BG     = (20,  20,  28)
POPUP_BORDER = (80,  220, 100)
POPUP_DONE   = (60,  80,  240)

FONT       = cv2.FONT_HERSHEY_DUPLEX
FONT_SMALL = cv2.FONT_HERSHEY_SIMPLEX

BUTTON_RECT = (20, PREVIEW_H - 70, 260, 50)

# ── Helpers ───────────────────────────────────────────────────────────────────
def draw_rounded_rect(img, x, y, w, h, r, color, thickness=-1):
    cv2.rectangle(img, (x+r, y),   (x+w-r, y+h),   color, thickness)
    cv2.rectangle(img, (x,   y+r), (x+w,   y+h-r), color, thickness)
    for cx, cy in [(x+r,y+r),(x+w-r,y+r),(x+r,y+h-r),(x+w-r,y+h-r)]:
        cv2.circle(img, (cx, cy), r, color, thickness)


def draw_popup(frame, lines, border_color, sub_line="Press  ENTER  to continue"):
    pw, ph = 580, 200
    px = (PREVIEW_W - pw) // 2
    py = (PREVIEW_H - ph) // 2

    # Dim background
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (PREVIEW_W, PREVIEW_H), (0, 0, 0), -1)
    frame[:] = cv2.addWeighted(overlay, 0.55, frame, 0.45, 0)

    # Popup box
    draw_rounded_rect(frame, px, py, pw, ph, 14, POPUP_BG, -1)
    draw_rounded_rect(frame, px, py, pw, ph, 14, border_color, 3)

    # Text lines
    y_cursor = py + 54
    for i, line in enumerate(lines):
        scale = 0.85 if i == 0 else 0.6
        color = WHITE if i == 0 else (180, 180, 180)
        tw = cv2.getTextSize(line, FONT, scale, 1)[0][0]
        cv2.putText(frame, line,
                    (px + pw//2 - tw//2, y_cursor),
                    FONT, scale, color, 1, cv2.LINE_AA)
        y_cursor += 46

    # Pulsing ENTER prompt
    if sub_line and int(time.time() * 2) % 2 == 0:
        tw = cv2.getTextSize(sub_line, FONT_SMALL, 0.55, 1)[0][0]
        cv2.putText(frame, sub_line,
                    (px + pw//2 - tw//2, py + ph - 20),
                    FONT_SMALL, 0.55, border_color, 1, cv2.LINE_AA)


def draw_hud(frame, session_idx, recording, elapsed, face_detected):
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (PREVIEW_W, 54), BG, -1)
    frame[:] = cv2.addWeighted(overlay, 0.82, frame, 0.18, 0)

    cv2.putText(frame, f"SESSION  {min(session_idx, TOTAL)}/{TOTAL}",
                (18, 34), FONT, 0.75, WHITE, 1, cv2.LINE_AA)

    dot_color = GREEN if face_detected else GRAY
    cv2.circle(frame, (PREVIEW_W//2, 27), 8, dot_color, -1)
    label = "FACE DETECTED" if face_detected else "NO FACE"
    tw = cv2.getTextSize(label, FONT_SMALL, 0.45, 1)[0][0]
    cv2.putText(frame, label,
                (PREVIEW_W//2 - tw//2, 48),
                FONT_SMALL, 0.45, dot_color, 1, cv2.LINE_AA)

    if recording:
        remaining = max(0.0, MAX_DURATION - elapsed)
        bar_w   = int((elapsed / MAX_DURATION) * 260)
        bar_x   = PREVIEW_W - 280
        bar_col = GREEN if remaining > 5 else AMBER if remaining > 2 else RED
        cv2.rectangle(frame, (bar_x, 14), (bar_x+260, 28), (50,50,60), -1)
        cv2.rectangle(frame, (bar_x, 14), (bar_x+bar_w, 28), bar_col, -1)
        cv2.putText(frame, f"REC  {remaining:05.2f}s",
                    (bar_x, 48), FONT_SMALL, 0.5, bar_col, 1, cv2.LINE_AA)
        if int(time.time() * 2) % 2 == 0:
            cv2.circle(frame, (bar_x-14, 21), 6, RED, -1)

    bx, by, bw, bh = BUTTON_RECT
    if recording:
        btn_color = (50, 50, 180)
        btn_text  = "Recording…  auto-stops at 15s"
    else:
        btn_color = (40, 100, 40)
        btn_text  = "[ ENTER ]  confirm popup"

    draw_rounded_rect(frame, bx, by, bw, bh, 8, btn_color, -1)
    draw_rounded_rect(frame, bx, by, bw, bh, 8, WHITE, 1)
    tw = cv2.getTextSize(btn_text, FONT_SMALL, 0.5, 1)[0][0]
    cv2.putText(frame, btn_text,
                (bx + bw//2 - tw//2, by + bh//2 + 6),
                FONT_SMALL, 0.5, WHITE, 1, cv2.LINE_AA)

    cv2.putText(frame, "Q = quit",
                (PREVIEW_W - 100, PREVIEW_H - 12),
                FONT_SMALL, 0.4, GRAY, 1, cv2.LINE_AA)


# ── DepthAI pipeline ──────────────────────────────────────────────────────────
def build_pipeline():
    pipeline = dai.Pipeline()

    # ColorCamera + MonoCamera (deprecated warnings are harmless, API still works)
    cam = pipeline.create(dai.node.ColorCamera)
    cam.setBoardSocket(dai.CameraBoardSocket.CAM_A)
    cam.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
    cam.setPreviewSize(PREVIEW_W, PREVIEW_H)
    cam.setInterleaved(False)
    cam.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
    cam.setFps(FPS)

    mono_l = pipeline.create(dai.node.MonoCamera)
    mono_r = pipeline.create(dai.node.MonoCamera)
    mono_l.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
    mono_r.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
    mono_l.setBoardSocket(dai.CameraBoardSocket.CAM_B)
    mono_r.setBoardSocket(dai.CameraBoardSocket.CAM_C)
    mono_l.setFps(FPS)
    mono_r.setFps(FPS)

    stereo = pipeline.create(dai.node.StereoDepth)
    stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.FAST_DENSITY)
    stereo.setDepthAlign(dai.CameraBoardSocket.CAM_A)
    stereo.setOutputSize(PREVIEW_W, PREVIEW_H)
    stereo.setLeftRightCheck(True)
    stereo.setSubpixel(False)
    mono_l.out.link(stereo.left)
    mono_r.out.link(stereo.right)

    face_det = pipeline.create(dai.node.MobileNetDetectionNetwork)
    face_det.setConfidenceThreshold(0.5)
    face_det.setBlobPath(
        dai.OpenVINO.getBlobLatestVersion(
            "face-detection-retail-0004",
            dai.OpenVINO.Version.VERSION_2022_1, 6,
        )
    )
    face_det.input.setBlocking(False)
    cam.preview.link(face_det.input)

    xout_rgb  = pipeline.create(dai.node.XLinkOut); xout_rgb.setStreamName("rgb")
    xout_dep  = pipeline.create(dai.node.XLinkOut); xout_dep.setStreamName("depth")
    xout_face = pipeline.create(dai.node.XLinkOut); xout_face.setStreamName("face")
    cam.preview.link(xout_rgb.input)
    stereo.depth.link(xout_dep.input)
    face_det.out.link(xout_face.input)

    return pipeline


def get_intrinsics(device):
    calib = device.readCalibration()
    M = calib.getCameraIntrinsics(dai.CameraBoardSocket.CAM_A, PREVIEW_W, PREVIEW_H)
    return {"fx": M[0][0], "fy": M[1][1],
            "cx": M[0][2], "cy": M[1][2],
            "width": PREVIEW_W, "height": PREVIEW_H}


def save_meta(path, intrinsics, session_idx, start_ts, end_ts, frames):
    with open(path, "w") as f:
        json.dump({
            **intrinsics,
            "session": session_idx,
            "started_at": start_ts, "ended_at": end_ts,
            "duration_s": round(end_ts - start_ts, 3),
            "frames": frames, "fps": FPS,
            "depth_aligned_to_color": True,
            "unproject_formula": "X=(u-cx)*Z/fx  Y=(v-cy)*Z/fy  (Z in mm)",
        }, f, indent=2)


def open_writers(stem):
    fourcc  = cv2.VideoWriter_fourcc(*"mp4v")
    w_color = cv2.VideoWriter(
        str(OUTPUT_DIR / f"{stem}_color.mp4"), fourcc, FPS, (PREVIEW_W, PREVIEW_H))
    w_depth = cv2.VideoWriter(
        str(OUTPUT_DIR / f"{stem}_depth.mp4"), fourcc, FPS, (PREVIEW_W, PREVIEW_H))
    return w_color, w_depth


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    pipeline = build_pipeline()

    WIN = "OAK-D Pro — RGBD Head Recorder"
    cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WIN, PREVIEW_W, PREVIEW_H)

    print(f"\n🎬  RGBD Head Recorder  |  {TOTAL} sessions × {MAX_DURATION}s  |  {FPS} fps")
    print(f"📁  Output → {OUTPUT_DIR.resolve()}\n")
    print("  ENTER = confirm popup   |   Q = quit\n")

    with dai.Device(pipeline) as device:
        intrinsics = get_intrinsics(device)
        q_rgb  = device.getOutputQueue("rgb",   maxSize=4, blocking=False)
        q_dep  = device.getOutputQueue("depth", maxSize=4, blocking=False)
        q_face = device.getOutputQueue("face",  maxSize=4, blocking=False)

        session_idx   = 1
        recording     = False
        rec_start     = None
        w_color       = None
        w_depth       = None
        depth_raw     = []
        stem          = None
        frame_count   = 0
        face_detected = False
        popup         = "ready"   # always start with ready popup

        while True:
            in_rgb  = q_rgb.get()
            in_dep  = q_dep.get()
            in_face = q_face.tryGet()

            color_frame = in_rgb.getCvFrame()
            depth_frame = in_dep.getFrame()

            if in_face is not None:
                dets = in_face.detections
                face_detected = len(dets) > 0
                if face_detected and recording:
                    det = max(dets, key=lambda d: d.confidence)
                    x1 = int(det.xmin * PREVIEW_W); y1 = int(det.ymin * PREVIEW_H)
                    x2 = int(det.xmax * PREVIEW_W); y2 = int(det.ymax * PREVIEW_H)
                    cv2.rectangle(color_frame, (x1,y1), (x2,y2), GREEN, 2)
                    cv2.circle(color_frame, ((x1+x2)//2, (y1+y2)//2), 5, RED, -1)

            elapsed = (time.time() - rec_start) if recording else 0.0

            # ── Auto-stop at 15s ───────────────────────────────────────────────
            if recording and elapsed >= MAX_DURATION:
                w_color.release()
                w_depth.release()
                np.save(str(OUTPUT_DIR / f"{stem}_depth_raw.npy"),
                        np.array(depth_raw, dtype=np.uint16))
                save_meta(OUTPUT_DIR / f"{stem}.json",
                          intrinsics, session_idx, rec_start, time.time(), frame_count)
                print(f"  ✅  Session {session_idx} complete — {frame_count} frames saved")
                recording = False

                if session_idx >= TOTAL:
                    popup = "all_done"
                    print(f"\n🎉  All {TOTAL} sessions recorded!")
                else:
                    popup = "done"

            # ── Write frames ───────────────────────────────────────────────────
            if recording:
                w_color.write(color_frame)
                depth_vis = (np.clip(depth_frame, 0, 8000).astype(np.float32)
                             / 8000 * 255).astype(np.uint8)
                w_depth.write(cv2.cvtColor(depth_vis, cv2.COLOR_GRAY2BGR))
                depth_raw.append(depth_frame.copy())
                frame_count += 1

            # ── HUD + popup ────────────────────────────────────────────────────
            draw_hud(color_frame, session_idx, recording, elapsed, face_detected)

            if popup == "ready":
                draw_popup(
                    color_frame,
                    lines=[
                        f"Ready for Session {session_idx} of {TOTAL}",
                        f"Duration: {int(MAX_DURATION)} seconds",
                    ],
                    border_color=POPUP_BORDER,
                    sub_line="Press  ENTER  to start recording",
                )
            elif popup == "done":
                draw_popup(
                    color_frame,
                    lines=[
                        f"Session {session_idx} complete  \u2713",
                        f"Next up: Session {session_idx + 1} of {TOTAL}",
                    ],
                    border_color=POPUP_DONE,
                    sub_line="Press  ENTER  for next session",
                )
            elif popup == "all_done":
                draw_popup(
                    color_frame,
                    lines=[
                        f"All {TOTAL} sessions recorded!",
                        "Saved to:  " + str(OUTPUT_DIR),
                    ],
                    border_color=AMBER,
                    sub_line="Press  Q  to exit",
                )

            cv2.imshow(WIN, color_frame)

            # ── Key input ──────────────────────────────────────────────────────
            key = cv2.waitKey(1) & 0xFF

            if key in (ord("q"), ord("Q")):
                if recording:
                    w_color.release()
                    w_depth.release()
                    print(f"\n⚠️   Quit mid-session — partial file may be incomplete.")
                break

            if key == 13:   # ENTER key
                if popup == "ready":
                    ts          = datetime.now().strftime("%Y%m%d_%H%M%S")
                    stem        = f"session_{session_idx:02d}_{ts}"
                    w_color, w_depth = open_writers(stem)
                    rec_start   = time.time()
                    frame_count = 0
                    depth_raw   = []
                    recording   = True
                    popup       = None
                    print(f"  ▶  Session {session_idx} started → {stem}")

                elif popup == "done":
                    session_idx += 1
                    popup = "ready"

                elif popup == "all_done":
                    break

    cv2.destroyAllWindows()
    print("\nDone.\n")


if __name__ == "__main__":
    main()
