import depthai as dai
import numpy as np
import cv2
import threading

# ======================
# GLOBAL STATE
# ======================
obstacle_left = False
obstacle_right = False

left_distance = 0.0     # mm
right_distance = 0.0    # mm

_running = True
_config = None


# ======================
# CAMERA THREAD
# ======================
def _camera_loop():
    global obstacle_left, obstacle_right
    global left_distance, right_distance
    global _running, _config

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

            roi_top = int(_config["TOP_IGNORE_RATIO"] * height)
            roi_bottom = int((1.0 - _config["BOTTOM_IGNORE_RATIO"]) * height)

            roi = depthFrame[roi_top:roi_bottom, :]

            # ===== LINKS =====
            left_roi = roi[:, :mid]
            valid_left = left_roi[left_roi > 0]

            if valid_left.size > 50:
                left_distance = float(np.percentile(valid_left, 20))
            else:
                left_distance = 0.0

            too_close_left = valid_left < _config["SIDE_DISTANCE"]
            left_ratio = (
                np.count_nonzero(too_close_left) / valid_left.size
                if valid_left.size > 0 else 0.0
            )

            # ===== RECHTS =====
            right_roi = roi[:, mid:]
            valid_right = right_roi[right_roi > 0]

            if valid_right.size > 50:
                right_distance = float(np.percentile(valid_right, 20))
            else:
                right_distance = 0.0

            too_close_right = valid_right < _config["SIDE_DISTANCE"]
            right_ratio = (
                np.count_nonzero(too_close_right) / valid_right.size
                if valid_right.size > 0 else 0.0
            )

            obstacle_left = left_ratio >= _config["SIDE_RATIO_THRESHOLD"]
            obstacle_right = right_ratio >= _config["SIDE_RATIO_THRESHOLD"]

            # ===== VISUALISATIE =====
            if _config["SHOW_DEBUG"]:
                depth_vis = cv2.normalize(depthFrame, None, 0, 255, cv2.NORM_MINMAX)
                depth_vis = np.uint8(depth_vis)
                depth_color = cv2.cvtColor(depth_vis, cv2.COLOR_GRAY2BGR)

                cv2.putText(depth_color, f"L: {int(left_distance)} mm", (40, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2)

                cv2.putText(depth_color, f"R: {int(right_distance)} mm", (40, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2)

                if obstacle_left:
                    cv2.putText(depth_color, "LEFT OBSTACLE", (40, 140),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

                if obstacle_right:
                    cv2.putText(depth_color, "RIGHT OBSTACLE", (40, 190),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

                cv2.imshow("OAK-D Side Avoidance", depth_color)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    _running = False
                    break

        cv2.destroyAllWindows()


# ======================
# PUBLIEKE API
# ======================
def start_camera_thread(config: dict):
    global _config
    _config = config
    thread = threading.Thread(target=_camera_loop, daemon=True)
    thread.start()


def stop_camera():
    global _running
    _running = False
