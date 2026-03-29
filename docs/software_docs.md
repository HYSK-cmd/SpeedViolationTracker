# 03-28-2026
## Created Polygon Drawer in util.py
### key:
    - left_click: create a point
    - right_click: complete shaping
    - r: reset shaping
    - s: display a masked image and save the roi image as the final image
    - q | esc: quit
### Key Functions:
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
