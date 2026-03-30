import os, cv2
import numpy as np
from dataclasses import dataclass

def get_first_frame(path:str) -> np.ndarray:
    cap = cv2.VideoCapture(path)
    _, frame = cap.read()
    if frame is None:
        raise FileNotFoundError("Image not found")
    frame = cv2.resize(frame, (1280, 720))
    return frame

# return type
@dataclass(frozen=True)
class ROI:
    xyxy: list[list]
    roi_image: np.ndarray

class Polygon:
    def __init__(self, image: np.ndarray):
        # display window
        self.original = image.copy()
        self.display = image.copy()
        self.points = []
        self.isClosed = False
        self.margin = 5

        # manual window
        self.bg_image = np.full((720, 600, 3), (255, 255, 255), dtype=np.uint8)
        self.adjust = 0

        # white background image for final image
        self.final_image = np.full((720, 1280, 3), (255, 255, 255), dtype=np.uint8)

        # return image
        self.masked_image = None

    def get_masked_roi_image(self):
        # create cv2 window
        cv2.namedWindow("draw a rectangle")
        cv2.namedWindow("manual")
        cv2.resizeWindow("draw a rectangle", 1280, 720)
        cv2.resizeWindow("manual", 500, 720)

        # create an example of a correct rectangle
        rec = [(250, 260), (350, 260), (370, 460), (230, 460)]
        pts = np.array([rec], dtype=np.int32)

        # draw trapezoid
        cv2.polylines(self.bg_image, [pts], isClosed=True, color=(0, 0, 0), thickness=2)

        # draw points
        for point in rec:
            cv2.circle(self.bg_image, point, 5, (0, 0, 0), -1)

        # label each vertex
        cv2.putText(self.bg_image, "Order: A->B->C->D", (180, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.putText(self.bg_image, "A", (rec[0][0] - 30, rec[0][1] - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.putText(self.bg_image, "B", (rec[1][0] + 20, rec[1][1] - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.putText(self.bg_image, "C", (rec[2][0] + 20, rec[2][1] + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.putText(self.bg_image, "D", (rec[3][0] - 30, rec[3][1] + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        cv2.setMouseCallback("draw a rectangle", self.mouse_callback, self)
        self.draw_rectangle()

        while True:
            cv2.imshow("draw a rectangle", self.display)
            cv2.imshow("manual", self.bg_image)
            option = cv2.waitKey(1) & 0xFF
            # reset
            if option == ord('r'):
                self.reset()
            # save the masked image
            elif option == ord('s'):
                # fewer vertices checking
                if len(self.points) != 5:
                    cv2.putText(self.display, "Must be a trapezoid or rectangle!",
                                (100, 360), cv2.FONT_HERSHEY_PLAIN, 4, (0, 255, 0), 5)
                    cv2.imshow("draw a rectangle", self.display)
                    # wait for one sec
                    cv2.waitKey(1000)
                    self.reset()
                # overlap checking
                elif not self.overlap():
                    cv2.putText(self.display, "The rectangle is not closed!",
                                (200, 360), cv2.FONT_HERSHEY_PLAIN, 4, (0, 255, 0),5)
                    cv2.imshow("draw a rectangle", self.display)
                    cv2.waitKey(1000)
                    self.reset()
                # when d is not pressed
                elif not self.isClosed:
                    cv2.putText(self.display, "Press d when finished!",
                                (200, 360), cv2.FONT_HERSHEY_PLAIN, 4, (0, 255, 0), 5)
                    cv2.imshow("draw a rectangle", self.display)
                    # wait for one sec
                    cv2.waitKey(1000)
                    self.reset()
                elif self.isClosed:
                    # create a fully black background
                    mask = np.zeros(self.original.shape[:2], dtype=np.uint8)
                    # create an array of selected vertices
                    vertices = np.array(self.points, dtype=np.int32)
                    # fill polygon in white
                    cv2.fillPoly(mask, [vertices], (255, 255, 255))
                    # keep only the polygon area from the white background image
                    roi_image = cv2.bitwise_and(self.original, self.original, mask=mask)
                    cv2.imshow("roi_image", roi_image)
                    # extract masked image
                    self.masked_image = cv2.bitwise_and(self.final_image, self.final_image, mask=mask)
                    cv2.imshow("masked_image", self.masked_image)
            # quit
            elif option == ord('q') or option == 27:
                break

        cv2.destroyAllWindows()
        if self.masked_image is None:
            raise RuntimeError("No roi image")
        # exclude the last point
        roi = ROI(self.points[:4], self.masked_image)
        return roi

    def draw_rectangle(self):
        # re-copy the original frame
        self.display = self.original.copy()
        # reset vertical offset for coordinate text rendering
        self.adjust = 0
        cv2.putText(self.bg_image, "l_click: point, r_click: done",
                    (10, 30), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 0),2)
        cv2.putText(self.bg_image, "r: reset, s: save, q or esc: quit",
                    (10, 70), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 2)
        self.adjust += 50
        # draw dots
        for p in self.points:
            cv2.circle(self.display, p, 5, (0, 0, 0), -1)
            cv2.putText(self.bg_image, f"{p[0], p[1]}",
                    (10, self.adjust+70), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 2)
            self.adjust += 40

        # create a line between dots
        if len(self.points) > 1:
            for i in range(len(self.points)-1):
                cv2.line(self.display, self.points[i], self.points[i+1], (0, 0, 255), 3)
        # connect the first and last dots if polygon is closed
        if len(self.points) > 2 and self.isClosed:
            cv2.line(self.display, self.points[-1], self.points[0], (0, 0, 255), 3)

    # check the overlapping for the first and last dots
    def overlap(self):
        x1, y1 = self.points[0]
        x2, y2 = self.points[-1]
        if abs(x1 - x2) > self.margin or abs(y1 - y2) > self.margin:
            return False
        return True

    # reset operation
    def reset(self):
        self.points = []
        self.isClosed = False
        self.bg_image = np.full((720, 600, 3), (255, 255, 255), dtype=np.uint8)
        self.draw_rectangle()

    @staticmethod
    # mouse event handler
    def mouse_callback(event, pt1, pt2, flags, param):
        self = param
        # left click to store coordinates
        if event == cv2.EVENT_LBUTTONDOWN and not self.isClosed:
            self.points.append([pt1, pt2])
            self.draw_rectangle()
        # right click to finish shaping a polygon
        elif event == cv2.EVENT_RBUTTONDOWN and not self.isClosed:
            self.isClosed = True


