import depthai as dai
import numpy as np
import cv2
from collections import deque

# ======================
# CONFIGURATIE
# ======================
THRESHOLD_DISTANCE = 500        # afstand tot stop in mm 
SAFE_FRAMES_TO_RESET = 15
ROI_RATIO = 0.9                 # Gebruik bovenste 70% van beeld
ROLLING_FRAMES = 10             # aantal frames voor gemiddelde
ROLLING_THRESHOLD = 0.5         # >50% frames te dichtbij → STOP

stop_active = False
safe_counter = 0
rolling_buffer = deque(maxlen=ROLLING_FRAMES)

# ======================
# PIPELINE
# ======================
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

# ======================
# RUN
# ======================
with dai.Device(pipeline) as device:
    depthQueue = device.getOutputQueue("depth", maxSize=4, blocking=False)
    print(">>> Depth fail-safe gestart <<<", flush=True)

    while True:
        inDepth = depthQueue.get()
        depthFrame = inDepth.getFrame()  # uint16, mm

        height, width = depthFrame.shape
        roi_height = int(ROI_RATIO * height)

        # ----------------------
        # ROI selecteren
        # ----------------------
        roi = depthFrame[0:roi_height, :]
        valid = roi > 0
        too_close = (roi < THRESHOLD_DISTANCE) & valid

        # ----------------------
        # Rolling buffer updaten
        # ----------------------
        rolling_buffer.append(too_close.any())

        # Gemiddelde te dichtbij over laatste N frames
        rolling_mean = np.mean(rolling_buffer)

        # ----------------------
        # FAIL-SAFE LOGICA
        # ----------------------
        if rolling_mean >= ROLLING_THRESHOLD:
            stop_active = True
            safe_counter = 0
        else:
            if stop_active:
                safe_counter += 1
                if safe_counter >= SAFE_FRAMES_TO_RESET:
                    stop_active = False
                    safe_counter = 0

        # ----------------------
        # Debug / min depth
        # ----------------------
        min_depth = np.min(roi[valid]) if np.any(valid) else 0

        # ----------------------
        # VISUALISATIE
        # ----------------------
        depth_vis = cv2.normalize(depthFrame, None, 0, 255, cv2.NORM_MINMAX)
        depth_vis = np.uint8(depth_vis)
        depth_color = cv2.cvtColor(depth_vis, cv2.COLOR_GRAY2BGR)

        # Te dichtbij pixels in ROI rood
        depth_color[0:roi_height, :][too_close] = [0, 0, 255]

        # ROI rechthoek tekenen
        cv2.rectangle(depth_color, (0,0), (width, roi_height), (255,255,0), 2)

        # Status overlay
        status_text = "STOP" if stop_active else "SAFE"
        status_color = (0,0,255) if stop_active else (0,255,0)
        cv2.putText(
            depth_color,
            status_text,
            (40, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            2.5,
            status_color,
            5
        )

        # Min depth overlay
        cv2.putText(
            depth_color,
            f"Min depth: {min_depth} mm",
            (40, 140),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255,255,255),
            2
        )

        # Rolling mean overlay
        cv2.putText(
            depth_color,
            f"Rolling mean: {rolling_mean:.2f}",
            (40, 180),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255,255,255),
            2
        )

        cv2.imshow("OAK-D Depth Fail-Safe", depth_color)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cv2.destroyAllWindows()
