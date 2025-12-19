import depthai as dai
import numpy as np
import cv2
import threading

# ======================
# CONFIGURATIE
# ======================
SIDE_DISTANCE = 1000          # mm → 2 meter
SIDE_RATIO_THRESHOLD = 0.03   # 3% pixels te dichtbij

TOP_IGNORE_RATIO = 0.05
BOTTOM_IGNORE_RATIO = 0.10

# ======================
# GLOBAL STATE
# ======================
obstacle_left = False
obstacle_right = False
_running = True


# ======================
# CAMERA THREAD
# ======================
def _camera_loop():
    global obstacle_left, obstacle_right, _running

    pipeline = dai.Pipeline()

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
        print(">>> OAK-D side avoidance gestart <<<", flush=True)

        while _running:
            inDepth = depthQueue.get()
            depthFrame = inDepth.getFrame()

            height, width = depthFrame.shape
            mid = width // 2

            roi_top = int(TOP_IGNORE_RATIO * height)
            roi_bottom = int((1.0 - BOTTOM_IGNORE_RATIO) * height)

            roi = depthFrame[roi_top:roi_bottom, :]

            # ===== LINKS =====
            left_roi = roi[:, :mid]
            valid_left = left_roi > 0
            too_close_left = (left_roi < SIDE_DISTANCE) & valid_left

            left_ratio = (
                np.count_nonzero(too_close_left) /
                np.count_nonzero(valid_left)
                if np.count_nonzero(valid_left) > 0 else 0.0
            )

            # ===== RECHTS =====
            right_roi = roi[:, mid:]
            valid_right = right_roi > 0
            too_close_right = (right_roi < SIDE_DISTANCE) & valid_right

            right_ratio = (
                np.count_nonzero(too_close_right) /
                np.count_nonzero(valid_right)
                if np.count_nonzero(valid_right) > 0 else 0.0
            )

            obstacle_left = left_ratio >= SIDE_RATIO_THRESHOLD
            obstacle_right = right_ratio >= SIDE_RATIO_THRESHOLD

            # ===== VISUALISATIE (OPTIONEEL) =====
            depth_vis = cv2.normalize(depthFrame, None, 0, 255, cv2.NORM_MINMAX)
            depth_vis = np.uint8(depth_vis)
            depth_color = cv2.cvtColor(depth_vis, cv2.COLOR_GRAY2BGR)

            if obstacle_left:
                cv2.putText(depth_color, "LEFT OBSTACLE", (40, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

            if obstacle_right:
                cv2.putText(depth_color, "RIGHT OBSTACLE", (40, 130),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

            cv2.imshow("OAK-D Side Avoidance", depth_color)

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
