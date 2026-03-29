import os, cv2
import numpy as np

def get_first_frame(path:str) -> np.ndarray:
    cap = cv2.VideoCapture(path)
    _, frame = cap.read()
    if frame is None:
        raise FileNotFoundError("Image not found")
    frame = cv2.resize(frame, (1280, 720))
    return frame

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
        self.roi_image = None

    def get_roi_image(self):
        # create cv2 window
        cv2.namedWindow("draw a polygon")
        cv2.namedWindow("manual")
        cv2.resizeWindow("draw a polygon", 1280, 720)
        cv2.resizeWindow("manual", 500, 720)
        cv2.setMouseCallback("draw a polygon", self.mouse_callback, self)
        self.draw_polygon()

        while True:
            cv2.imshow("draw a polygon", self.display)
            cv2.imshow("manual", self.bg_image)
            option = cv2.waitKey(1) & 0xFF
            # reset
            if option == ord('r'):
                self.reset()
            # save the masked image
            elif option == ord('s'):
                # fewer vertices checking
                if len(self.points) < 3:
                    cv2.putText(self.display, "You must draw a polygon!",
                                (200, 360), cv2.FONT_HERSHEY_PLAIN, 4, (0, 255, 0), 5)
                    cv2.imshow("draw a polygon", self.display)
                    # wait for one sec
                    cv2.waitKey(1000)
                    self.reset()
                # overlap checking
                elif not self.overlap():
                    cv2.putText(self.display, "The polygon is not closed!",
                                (200, 360), cv2.FONT_HERSHEY_PLAIN, 4, (0, 255, 0),5)
                    cv2.imshow("draw a polygon", self.display)
                    cv2.waitKey(1000)
                    self.reset()
                # when d is not pressed
                elif not self.isClosed:
                    cv2.putText(self.display, "Press d when finished!",
                                (200, 360), cv2.FONT_HERSHEY_PLAIN, 4, (0, 255, 0), 5)
                    cv2.imshow("draw a polygon", self.display)
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
                    masked_image = cv2.bitwise_and(self.original, self.original, mask=mask)
                    cv2.imshow("masked_image", masked_image)
                    # extract roi
                    self.roi_image = cv2.bitwise_and(self.final_image, self.final_image, mask=mask)
                    cv2.imshow("roi_image", self.roi_image)
            # quit
            elif option == ord('q') or option == 27:
                break

        cv2.destroyAllWindows()
        if self.roi_image is None:
            raise RuntimeError("No roi image")
        return self.roi_image

    def draw_polygon(self):
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
        self.draw_polygon()

    @staticmethod
    # mouse event handler
    def mouse_callback(event, pt1, pt2, flags, param):
        self = param
        # left click to store coordinates
        if event == cv2.EVENT_LBUTTONDOWN and not self.isClosed:
            self.points.append((pt1, pt2))
            self.draw_polygon()
        # right click to finish shaping a polygon
        elif event == cv2.EVENT_RBUTTONDOWN and not self.isClosed:
            self.isClosed = True


