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
## Polygon Drawer -> Trapezoid Drawer
### Modifications in util.py
    - Changed shaping policies
        - The shape must either be a trapezoid or rectangle
    - Added the simple tutorial to pick points in a sorted manner
    - Added a new dataclass consisting of a list of points and a roi image
## New Features in detection_for_video.py
    - Added new arguments roi to the main function (type=dataclass)
    - Added a new class "ViewTransformer" for speed estimation
## New file "download_video.py"
    - Created a new py file that downloads the testing video from supervision library

# 03-31-2026
## Modifications in util.py
    *The util.py simply returns the four selected points from an image*
    - Removed self.masked, self.margin
    - Removed overlap function
    - Removed resizing the original frame
    - Instead:
        - Set fixed resolution -> (1280, 720)
        - Defined original resolution -> (X, Y)
    - Created a separate module for displaying instruction
    **IMPORTANT**
        - The resizing frame does not pixelate to corresponding resolution
        - Only the drawing window is resized 
        - Only thing to consider is that the points should be carefully selected if original frame > (1280, 720)
    - Only allowed for choosing 4 points as the last line will be automatically connected
    - Changed dataclass elements
        - points: list
        - real_w, real_h: float
    
## Modifications in settings.yaml
    - Removed unncessary config variables

## Renamed detection_for_video -> video_speed_detector
    - Decoupled the ViewTransformer class into sub-modules for the VideoDetection class
```python
def _get_perspective_trans():
    ...
    pass
def _transform_points():
    ...
    pass
def _calculate_inv_scale():
    ...
    pass
```
    - _get_perspective_trans() -> args: source roi polygon matrix and bird eye's view matrix
    - _transform_points() -> args: bottom center of bbox of detected objects
    - _calculate_inv_scale() -> args: original frame and bbox
    - Created a generator function for frame reading to save memory 
    - Added VideoWriter to save a video output 
    - Upper/lower base are a replacement for line A/B
    - Changed logics in speed estimation, memory management, and text indicators
    - Added a semi-transparent color over speed estimation area

## Modifications in script.py
    - Added an extra option for output_video_path