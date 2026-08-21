# 🌱 PlantGuard AI - Complete System Flow Diagram

## 📊 Overview Flow (Touch-Triggered Pump Control)

```mermaid
graph TD
    A[👤 Person Touches Sensor] --> B[ESP32 Touch Event]
    B --> C[Serial: 'TOUCHED' Command]
    C --> D[Python Serial Listener]
    D --> E[Touch Workflow Orchestrator]
    E --> F[Background Thread Execution]
    F --> G[🔊 TTS: 'Sensor Touched']
    G --> H[📸 Capture Snapshot]
    H --> I[🎥 Record Video Clip]
    I --> J[🔍 YOLO Person Detection]
    J --> K{Person Detected?}
    K -->|Yes| L[💧 Send Pump Command]
    K -->|No| M[❌ No Pump Action]
    L --> N[ESP32 Pump Activation]
    N --> O[💦 Water Transfer 2s]
    O --> P[⏸️ 60s Cooldown]
    M --> Q[💾 Save to Database]
    P --> Q
    Q --> R[🤖 Queue VLM Analysis]
    R --> S[📱 UI Update: Thumbnail + Video Badge]
```

## 🔧 Detailed Component Flow

### 1. Hardware Layer (ESP32)

```mermaid
graph LR
    A[Touch Sensor GPIO4] --> B[ESP32 Core]
    B --> C[Debounce Logic]
    C --> D[Serial Output: 'TOUCHED']
    E[HDC302x Sensor] --> F[I2C Data]
    F --> G[Temp/Humidity JSON]
    H[Pump Relay GPIO] --> I[Water Pump]
    I --> J[Container A → Container B]
    K[LED GPIOs] --> L[Status Indicators]
```

### 2. Software Layer (Python Backend)

```mermaid
graph TB
    A[serial_unified_listener.py] --> B[Parse Serial Data]
    B --> C{Message Type?}
    C -->|'TOUCHED'| D[handle_touch_event()]
    C -->|Sensor JSON| E[insert_sensor_reading()]
    D --> F[TouchWorkflowOrchestrator]
    F --> G[Background Thread]
    G --> H[_run_workflow()]
    H --> I[_capture_snapshot()]
    I --> J[capture_webcam_image()]
    H --> K[_record_video()]
    K --> L[record_video_alert()]
    H --> M[_run_yolo()]
    M --> N[process_image_for_person_detection()]
    N --> O{person_detected?}
    O -->|True| P[_trigger_pump()]
    O -->|False| Q[Skip Pump]
    P --> R[ser.write('PUMP_ON_YELLOW_LEAVES')]
    H --> S[_save_to_database()]
    S --> T[insert_snapshot_quick()]
    H --> U[_queue_vlm_analysis()]
```

### 3. Database Flow

```mermaid
graph LR
    A[Snapshot Image] --> B[plant_snapshots Table]
    C[Video File] --> B
    D[YOLO Metadata] --> B
    E[Boxed Image Path] --> B
    F[Sensor Data] --> B
    B --> G[VLM Worker Queue]
    G --> H[Background Analysis]
    H --> I[Update VLM Results]
```

### 4. UI/Visualization Flow

```mermaid
graph TB
    A[Database Update] --> B[React Frontend]
    B --> C[Real-time Refresh]
    C --> D[Snapshot Gallery]
    D --> E[Thumbnail Display]
    E --> F[🎥 Video Badge]
    F --> G[Click to Open Detail]
    G --> H[Image + Bounding Boxes]
    H --> I[Video Player]
    I --> J[VLM Analysis Results]
```

## 🚀 Complete End-to-End Flow

```mermaid
sequenceDiagram
    participant Person
    participant ESP32
    participant Python
    participant Camera
    participant YOLO
    participant Pump
    participant Database
    participant UI

    Person->>ESP32: Touch sensor
    ESP32->>Python: Serial: 'TOUCHED'
    Python->>Python: Start workflow (async)
    Python->>Person: 🔊 TTS: 'Sensor touched'
    Python->>Camera: Capture image
    Camera->>Python: Image file
    Python->>Camera: Record video (3s)
    Camera->>Python: Video file
    Python->>YOLO: Detect person
    YOLO->>Python: person_detected=True/False
    
    alt Person Detected
        Python->>ESP32: Serial: 'PUMP_ON_YELLOW_LEAVES'
        ESP32->>Pump: Activate for 2s
        Pump->>ESP32: Water transferred
        ESP32->>Python: Pump complete
    else No Person
        Python->>Python: Skip pump
    end
    
    Python->>Database: Save snapshot + metadata
    Database->>Python: Saved with video_path
    Python->>Database: Queue VLM analysis
    Database->>UI: Real-time update
    UI->>Person: New thumbnail with video badge
```

## ⚙️ Configuration & Decision Points

### Video Recording Configuration
```mermaid
graph TD
    A[Touch Event] --> B{TOUCH_VIDEO_ENABLED?}
    B -->|true| C[Record 3s Video @10fps]
    B -->|false| D[Skip Video]
    C --> E[Save as .mp4]
    E --> F[Add video_path to DB]
    D --> G[Faster workflow]
```

### Pump Decision Logic
```mermaid
graph TD
    A[YOLO Complete] --> B{person_detected?}
    B -->|True| C[Log: 'Person detected']
    C --> D[Log: 'PUMP STATE: Will be turned ON']
    D --> E[Send pump command]
    B -->|False| F[Log: 'No person detected']
    F --> G[Log: 'PUMP STATE: Will remain OFF']
```

### Database Storage Flow
```mermaid
graph LR
    A[Image File] --> B[plant_snapshots.image_path]
    C[Video File] --> B[plant_snapshots.video_path]
    D[YOLO Result] --> B[plant_snapshots.detection_metadata]
    E[Boxed Image] --> B[plant_snapshots.boxed_image_path]
    F[Sensor Data] --> B[plant_snapshots.temperature_c]
    F --> B[plant_snapshots.humidity_pct]
    G[VLM Queue] --> B[plant_snapshots.analysis_status='queued']
```

## 🔄 Continuous Monitoring Flow (Non-Touch Events)

```mermaid
graph TD
    A[ESP32 Temperature Loop] --> B[Serial: Sensor JSON]
    B --> C[Python: parse_sensor_data()]
    C --> D[Database: insert_sensor_reading()]
    D --> E[UI: Update live charts]
    E --> F[Check Temperature Threshold]
    F --> G{Temp >= 25°C?}
    G -->|Yes| H[🔥 Temperature Alert]
    G -->|No| I[Continue Monitoring]
    H --> J[DISABLED: No auto-snapshot]
    J --> I
```

## 📱 UI Component Interaction

```mermaid
graph TB
    A[Snapshot Gallery] --> B[Thumbnail Grid]
    B --> C[Image Preview]
    C --> D[🎥 Video Badge]
    D --> E[Click Video]
    E --> F[Video Modal]
    F --> G[Play/Pause Controls]
    C --> H[Click Image]
    H --> I[Detail View]
    I --> J[Bounding Boxes]
    J --> K[VLM Analysis]
    K --> L[Plant Health Info]
```

## 🚨 Error Handling Flow

```mermaid
graph TD
    A[Workflow Start] --> B{Camera Available?}
    B -->|No| C[Log: Camera error]
    B -->|Yes| D[Capture Image]
    D --> E{YOLO Available?}
    E -->|No| F[Log: YOLO error]
    E -->|Yes| G[Run Detection]
    G --> H{Database Available?}
    H -->|No| I[Log: DB error]
    H -->|Yes| J[Save Results]
    C --> K[Workflow Failed]
    F --> K
    I --> K
    J --> L[Workflow Complete]
```

## 📊 Performance Metrics Flow

```mermaid
graph LR
    A[Touch Event] --> B[Start Timer]
    B --> C[Capture: ~1s]
    C --> D[Video: ~3s]
    D --> E[YOLO: ~10-12s]
    E --> F[DB Save: ~0.5s]
    F --> G[Total: ~15s]
    G --> H[UI Update: Immediate]
    H --> I[Pump Trigger: Immediate after YOLO]
```

---

## 🎯 Key Features Illustrated

1. **Non-blocking Architecture**: Serial listener continues working while workflow runs in background
2. **Smart Decision Making**: Pump only activates when person is detected
3. **Rich Data Capture**: Image + video + YOLO metadata + VLM analysis
4. **Real-time UI**: Immediate updates with video badges and thumbnails
5. **Robust Error Handling**: Graceful degradation when components fail
6. **Configurable Performance**: Video recording can be disabled for speed
7. **Comprehensive Logging**: Full audit trail of all decisions and actions

This flow diagram represents the complete PlantGuard AI system from human interaction to automated plant care! 🌱🤖💧
