# Project 2 - Car Speed Detector

## 목표
영상에서 차량의 속도를 측정하고, 제한 속도 초과 시 해당 차량 프레임을 캡쳐 저장

## 속도 계산 원리
```
Line A ──────────────────  ← y좌표 고정
         ↕ real_dist_m (예: 10m)
Line B ──────────────────  ← y좌표 고정

speed_kmh = (real_dist_m / (t2 - t1)) * 3.6
```

---

## 세부 구현 계획

### STEP 1. 프로젝트 세팅
- `Project 2 - Speed Detector/` 폴더 생성
- `Speed-Detector.py` 파일 생성
- `captures/` 폴더 생성 (캡쳐 이미지 저장용)
- imports: `YOLO, cv2, cvzone, math, time, torch, os`
- 상수 정의:
  ```python
  SPEED_LIMIT = 80       # km/h 제한속도
  REAL_DIST_M = 10       # 두 선 사이 실제 거리(미터) — 영상 보고 조정
  LINE_A_Y = 300         # Line A의 y좌표 — 영상 보고 조정
  LINE_B_Y = 500         # Line B의 y좌표 — 영상 보고 조정
  ```

### STEP 2. YOLO + ByteTrack 추적
- `model.track()`으로 ID 포함 추적
  ```python
  results = model.track(image, stream=True, device=device, persist=True)
  ```
- `box.id`로 차량 고유 ID 추출
  ```python
  if box.id is not None:
      car_id = int(box.id[0])
  ```
- `persist=True` 필수 — 프레임 간 ID 유지

### STEP 3. 두 기준선 시각화
- 매 프레임마다 Line A, B 그리기
  ```python
  cv2.line(image, (0, LINE_A_Y), (frame_width, LINE_A_Y), (0, 255, 0), 2)
  cv2.line(image, (0, LINE_B_Y), (frame_width, LINE_B_Y), (255, 0, 0), 2)
  ```

### STEP 4. 차량별 타임스탬프 딕셔너리
- 딕셔너리 구조:
  ```python
  car_times = {}
  # 예: {3: {'lineA': 1.52}, 3: {'lineA': 1.52, 'lineB': 1.89}}
  ```
- bbox 중심 y좌표가 Line A/B를 통과하는지 체크
  ```python
  cy = (y1 + y2) // 2  # bbox 중심
  if abs(cy - LINE_A_Y) < 5 and car_id not in car_times:
      car_times[car_id] = {'lineA': time.time()}
  if abs(cy - LINE_B_Y) < 5 and car_id in car_times and 'lineB' not in car_times[car_id]:
      car_times[car_id]['lineB'] = time.time()
  ```
- `< 5` 오차 범위로 선 통과 감지

### STEP 5. 속도 계산
- lineA, lineB 둘 다 기록된 차량만 계산
  ```python
  if 'lineA' in car_times.get(car_id, {}) and 'lineB' in car_times.get(car_id, {}):
      t = car_times[car_id]['lineB'] - car_times[car_id]['lineA']
      speed = (REAL_DIST_M / t) * 3.6
  ```

### STEP 6. 제한속도 초과 시 캡쳐
- 속도 계산 직후 체크
  ```python
  if speed > SPEED_LIMIT:
      filename = f"captures/car_{car_id}_{int(speed)}kmh.jpg"
      cv2.imwrite(filename, image)
  ```
- 한 차량당 한 번만 저장되도록 `car_times[car_id]['saved'] = True` 플래그 사용

### STEP 7. UI 표시
- bbox 위에 ID + 속도 텍스트
  ```python
  color = (0, 0, 255) if speed > SPEED_LIMIT else (0, 255, 0)
  cvzone.putTextRect(image, f"ID:{car_id} {int(speed)}km/h", (x1, y1-10), ...)
  ```
- 제한속도 초과 시 빨간색, 정상 시 초록색

### STEP 8. argparse — 입력 소스 선택
- 비디오 파일 또는 라이브 스트림 선택
  ```bash
  python Speed-Detector.py --source video       # 저장된 영상
  python Speed-Detector.py --source stream      # 라이브 스트림 (추후 구현)
  python Speed-Detector.py --file cars.mp4      # 영상 파일 경로 지정
  ```
- 코드:
  ```python
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('--source', choices=['video', 'stream'], default='video')
  parser.add_argument('--file', default='../videos/cars.mp4')
  args = parser.parse_args()
  ```

### STEP 9. 자동 Edge Detection → Mask 생성
- 첫 프레임에서 도로 영역 자동 감지
  ```python
  gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
  edges = cv2.Canny(gray, 50, 150)
  # 관심 영역(ROI) 폴리곤으로 마스크 생성
  mask = np.zeros_like(gray)
  polygon = np.array([[...]])  # Canny 결과 기반 자동 추정
  cv2.fillPoly(mask, polygon, 255)
  ```
- 마스크에서 도로 방향을 분석해 **Line A, B y좌표 자동 계산**
  - 도로 상단 1/3 지점 → Line A
  - 도로 하단 1/3 지점 → Line B

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

## 하드웨어 계획 (추후)
| 장치 | 역할 |
|------|------|
| Raspberry Pi 4 | 엣지 디바이스로 현장 실행 |
| Raspberry Camera | 라이브 영상 입력 |
| Piezo Buzzer / LED | 속도 위반 시 경고음/경고등 |

> ⚠️ 라이브 스트림 및 하드웨어 연동은 **저장된 영상 구현 완료 후** 진행

---

## 구현 순서 (Phase)
- **Phase 1 (현재)**: 저장된 영상(`cars.mp4`)으로 속도 측정 + 캡쳐
- **Phase 2**: 웹 UI 대시보드
- **Phase 3**: 라이브 스트림 + Raspberry Pi 연동

---

## 고려사항
- `REAL_DIST_M`, `LINE_A_Y`, `LINE_B_Y` 는 Edge Detection으로 자동 추정, 수동 보정 가능
- `cars.mp4` 영상 재사용 가능
- ByteTrack은 ultralytics에 내장되어 있어 별도 설치 불필요
- 캡쳐 이미지: `captures/car_{id}_{speed}kmh.jpg`
- Speedometer Device for comparison