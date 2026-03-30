# 03-28-2026
## Created Polygon Drawer in util.py
### key:
    - left_click: create a point
    - right_click: complete shaping
    - r: reset shaping
    - s: display a masked image and save the roi image as the final image
    - q | esc: quit
## Key Functions:
```bash
def get_roi_image(self) -> extracts roi image from the original image
def draw_polygon(self) -> executes polygon drawer program using cv2
```
    - Polygon Validator
      - checks the number of vertices
      - checks the overlapping
      - checks the completeness of a shape
    - Auxiliary Helper Window
      - display each key's instruction
      - display selected points (x, y)
## Created docs to keep track of updates 
    - general_docs.md
        - document the key update of the system and future plans
    - software_docs.md
        - document the detailed explanations of changes/rectifications/improvements in software system
    - hardware_docs.md
        - document the detailed explanations of changes/rectifications/improvements in hardware system

# 03-29-2026
## Polygon Drawer -> Rectangle Drawer
### Modifications in util.py
    - Changed shaping policies
        - The shape must either be a trapezoid or rectangle
    - Added the simple tutorial to pick points in a sorted manner
    - Added a new dataclass consisting of a list of points and a roi image
### New Features in detection_for_video.py
    - Added new arguments roi to the main function (type=dataclass)
    - Added a new class "ViewTransformer" for speed estimation
### New file "download_video.py"
    - Created a new py file that downloads the testing video from supervision library