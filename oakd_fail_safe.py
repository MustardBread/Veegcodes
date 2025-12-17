import depthai as dai
import numpy as np
import cv2
from collections import deque
import threading

# ======================
# CONFIGURATIE
# ======================
THRESHOLD_DISTANCE = 500        # mm → STOP als object dichterbij is
SAFE_FRAMES_TO_RESET = 15       # aantal veilige frames om STOP op te heffen

ROLLING_FRAMES = 10             # rolling window lengte
ROLLING_THRESHOLD = 0.5         # >50% gevaar-frames → STOP

PIXEL_RATIO_THRESHOLD = 0.02    # minimaal % pixels te dichtbij (2%)

TOP_IGNORE_RATIO = 0.05         # bovenste 5% negeren
BOTTOM_IGNORE_RATIO = 0.10      # onderste 10% negeren

# ======================
# GLOBAL STATE
# ======================
stop_active = False
_running = True

rolling_buffer = deque(maxlen=ROLLING_FRAMES)
safe_counter = 0


# ======================
# CAMERA THREAD
# ======================
def _camera_loop():
    global stop_active, safe_counter, _running

    pipeline = dai.Pipeline()

    # ---- Camera setup ----
    monoLeft = pipeline.createMonoCamera()
    monoRight = pipeline.createMonoCamera()
    stereo = pipeline.createStereoDepth()

    monoLeft.setBoardSocket(dai.CameraBoardSocket.CAM_B)
    monoRight.setBoardSocket(dai.CameraBoardSocket.CAM_C)

    monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_720_P)
    monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_720_P)

    stereo.setLeftRightCheck(True)
    stereo.setExtendedDisparity(True)

    monoLeft.out.link(stereo.left)
    monoRight.out.link(stereo.right)

    xoutDepth = pipeline.createXLinkOut()
    xoutDepth.setStreamName("depth")
    stereo.depth.link(xoutDepth.input)

    with dai.Device(pipeline) as device:
        depthQueue = device.getOutputQueue("depth", maxSize=4, blocking=False)
        print(">>> OAK-D fail-safe camera gestart <<<", flush=True)

        while _running:
            inDepth = depthQueue.get()
            depthFrame = inDepth.getFrame()  # uint16 (mm)

            height, width = depthFrame.shape

            # ======================
            # ROI BEREKENING
            # ======================
            roi_top = int(TOP_IGNORE_RATIO * height)
            roi_bottom = int((1.0 - BOTTOM_IGNORE_RATIO) * height)

            roi = depthFrame[roi_top:roi_bottom, :]
            valid = roi > 0
            too_close = (roi < THRESHOLD_DISTANCE) & valid

            # ======================
            # PIXEL-MARGE LOGICA
            # ======================
            total_valid_pixels = np.count_nonzero(valid)
            too_close_pixels = np.count_nonzero(too_close)

            if total_valid_pixels > 0:
                close_ratio = too_close_pixels / total_valid_pixels
            else:
                close_ratio = 0.0

            danger_frame = close_ratio >= PIXEL_RATIO_THRESHOLD

            # ======================
            # ROLLING FAIL-SAFE
            # ======================
            rolling_buffer.append(danger_frame)
            rolling_mean = np.mean(rolling_buffer)

            if rolling_mean >= ROLLING_THRESHOLD:
                stop_active = True
                safe_counter = 0
            else:
                if stop_active:
                    safe_counter += 1
                    if safe_counter >= SAFE_FRAMES_TO_RESET:
                        stop_active = False
                        safe_counter = 0

            # ======================
            # VISUALISATIE
            # ======================
            depth_vis = cv2.normalize(depthFrame, None, 0, 255, cv2.NORM_MINMAX)
            depth_vis = np.uint8(depth_vis)
            depth_color = cv2.cvtColor(depth_vis, cv2.COLOR_GRAY2BGR)

            # Te dichtbij pixels rood kleuren
            depth_color[roi_top:roi_bottom, :][too_close] = [0, 0, 255]

            # ROI kader
            cv2.rectangle(
                depth_color,
                (0, roi_top),
                (width, roi_bottom),
                (255, 255, 0),
                2
            )

            # Status
            status_text = "STOP" if stop_active else "SAFE"
            status_color = (0, 0, 255) if stop_active else (0, 255, 0)

            cv2.putText(
                depth_color,
                status_text,
                (40, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                2.5,
                status_color,
                5
            )

            # Debug info
            cv2.putText(
                depth_color,
                f"Rolling mean: {rolling_mean:.2f}",
                (40, 140),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (255, 255, 255),
                2
            )

            cv2.putText(
                depth_color,
                f"Close ratio: {close_ratio*100:.1f}%",
                (40, 180),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (255, 255, 255),
                2
            )

            cv2.imshow("OAK-D Depth Fail-Safe", depth_color)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                _running = False
                break

        cv2.destroyAllWindows()


# ======================
# PUBLIEKE API
# ======================
def start_camera_thread():
    thread = threading.Thread(target=_camera_loop, daemon=True)
    thread.start()


def stop_camera():
    global _running
    _running = False
