import os, cv2
import numpy as np

def get_first_frame(path:str) -> np.ndarray:
    cap = cv2.VideoCapture(path)
    _, frame = cap.read()
    return frame

# GaussianBlur
# BGR → HSV
# inRange()로 특정 색만 마스크
# Canny
# HoughLinesP
def nothing(x):
    pass
def filter_image(img:np.ndarray) -> np.ndarray:
    #img = cv2.imread(os.path.join("assets/videos/cars02.jpg"))
    if img is not None:
        # resize if not matched
        img = cv2.resize(img, (1280, 720))

        # use Gaussian Blur
        blur = cv2.GaussianBlur(img, (3, 3), 7)

        # convert to HSV colorspace
        # more intuitive and less sensitive to lighting variations
        # img_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)

        # trackbars for tuning
        cv2.namedWindow("Trackbars")
        cv2.createTrackbar("H Min", "Trackbars", 0, 179, nothing)
        cv2.createTrackbar("H Max", "Trackbars", 179, 179, nothing)
        cv2.createTrackbar("S Min", "Trackbars", 0, 255, nothing)
        cv2.createTrackbar("S Max", "Trackbars", 80, 255, nothing)
        cv2.createTrackbar("V Min", "Trackbars", 40, 255, nothing)
        cv2.createTrackbar("V Max", "Trackbars", 210, 255, nothing)

        while True:
            h_min = cv2.getTrackbarPos("H Min", "Trackbars")
            h_max = cv2.getTrackbarPos("H Max", "Trackbars")
            s_min = cv2.getTrackbarPos("S Min", "Trackbars")
            s_max = cv2.getTrackbarPos("S Max", "Trackbars")
            v_min = cv2.getTrackbarPos("V Min", "Trackbars")
            v_max = cv2.getTrackbarPos("V Max", "Trackbars")

            lower = np.array([h_min, s_min, v_min])
            upper = np.array([h_max, s_max, v_max])

            # HSV mask
            mask = cv2.inRange(hsv, lower, upper)

            # morphology to remove noise
            kernel = np.ones((7, 7), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

            # find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            road_mask = np.zeros_like(mask)

            if contours:
                # keep the largest region as road candidate
                largest = max(contours, key=cv2.contourArea)

                if cv2.contourArea(largest) > 5000:
                    cv2.drawContours(road_mask, [largest], -1, 255, thickness=cv2.FILLED)

            # extract only road region
            road_only = cv2.bitwise_and(img, img, mask=road_mask)

            # overlay
            overlay = np.zeros_like(img)
            overlay[road_mask > 0] = (255, 255, 255)
            result = overlay

            cv2.imshow("Original", img)
            cv2.imshow("Road Mask", road_mask)
            cv2.imshow("Road Only", road_only)
            cv2.imshow("Overlay", result)

            key = cv2.waitKey(1)
            if key == 27:  # ESC
                break

        cv2.destroyAllWindows()

