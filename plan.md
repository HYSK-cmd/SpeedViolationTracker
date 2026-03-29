
### STEP 10. 웹 UI (Simple Web Dashboard)
- **Flask** 로 웹 서버 구동
- 실시간 영상: **MJPEG streaming** 방식
  ```python
  def generate_frames():
      while True:
          success, frame = cap.read()
          # YOLO 처리...
          _, buffer = cv2.imencode('.jpg', frame)
          yield (b'--frame\r\n'
                 b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            A = time.time()
            end = B - time.time() -> time_s distance_m -> 오로지 이미지만으로 측정하거나 
  @app.route('/video_feed')
  def video_feed():
      return Response(generate_frames(),
                      mimetype='multipart/x-mixed-replace; boundary=frame')
  ```
- HTML에서 `<img src="/video_feed">` 태그 하나로 실시간 스트림 표시
- 기능:
  - 실시간 처리 영상 스트리밍 (`/video_feed`)
  - 속도 위반 차량 목록 표시
  - `captures/` 폴더의 캡쳐 이미지 갤러리
  - 버튼으로 저장된 위반 차량 사진 열람
- 페이지 구성:
  ```
  [Live Feed]          [Violations]
  +-----------+        +------------------+
  | 영상 스트림 |        | car_3_95kmh.jpg  |
  |           |        | car_7_102kmh.jpg |
  +-----------+        | ...              |
                       | [사진 보기 버튼]   |
                       +------------------+
  ```

---