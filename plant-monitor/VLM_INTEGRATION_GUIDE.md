# 🤖 Local VLM Integration Guide

## Complete AI Reasoning Layer for Plant Monitoring System

---

## 📋 Table of Contents

1. [Model Recommendation](#model-recommendation)
2. [Architecture Overview](#architecture-overview)
3. [Installation & Setup](#installation--setup)
4. [Implementation Roadmap](#implementation-roadmap)
5. [Module Documentation](#module-documentation)
6. [API Reference](#api-reference)
7. [React Components](#react-components)
8. [Testing & Validation](#testing--validation)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Features](#advanced-features)

---

## 🎯 Model Recommendation

### **Recommended: Ollama + LLaVA 1.6 (7B)**

**Why This Choice:**

| Feature | Qwen2.5-VL | LLaVA-OneVision | **Ollama + LLaVA** ⭐ |
|---------|------------|-----------------|----------------------|
| Setup Complexity | High (manual install) | High (manual install) | **Low (one command)** |
| Memory Usage | 16GB+ VRAM | 14GB+ VRAM | **8GB (7B model)** |
| API Interface | Python only | Python only | **REST API built-in** |
| Structured Output | Good | Good | **Excellent** |
| Video Support | Native | Native | Frame-by-frame |
| Local-first | ✅ Yes | ✅ Yes | ✅ **Yes + Easy** |
| Swappable Backend | Medium effort | Medium effort | **Easy (REST API)** |
| Production Ready | Research | Research | **Production** |

**Key Advantages:**
- ✅ **One-command installation** - No complex setup
- ✅ **REST API** - Easy to swap models without code changes
- ✅ **Low memory** - Runs on most laptops (8GB RAM)
- ✅ **Structured prompts** - Reliable JSON output
- ✅ **Active community** - Well-maintained and documented

---

## 🏗️ Architecture Overview

### **Data Flow Diagram**

```
┌──────────────────────────────────────────────────────────────────┐
│                  TEMPERATURE TRIGGER (≥25°C)                     │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    CAPTURE PIPELINE                              │
│  capture_with_vlm.py                                             │
│  ├─ Webcam → raw image (1280x720 JPEG)                          │
│  └─ Record → 5s video (MP4 H.264)                               │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    YOLO DETECTION                                │
│  detect_person.py                                                │
│  ├─ Detect people (YOLOv8n)                                      │
│  ├─ Draw bounding boxes                                          │
│  └─ Generate metadata JSON                                       │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                  VLM REASONING LAYER                             │
│  vlm/vlm_analyzer.py                                             │
│  ├─ Image Analysis:                                              │
│  │  ├─ Send to Ollama LLaVA (REST API)                          │
│  │  ├─ Use structured prompt template                           │
│  │  └─ Parse JSON response                                      │
│  │                                                               │
│  └─ Video Analysis:                                              │
│     ├─ Sample 5 frames uniformly                                │
│     ├─ Analyze representative frame                             │
│     └─ Generate event summary                                   │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                  INTELLIGENT RULES ENGINE                        │
│  vlm/analysis_rules.py                                           │
│  ├─ Check person occlusion → reliability                         │
│  ├─ Check image quality → usability                              │
│  ├─ Cross-validate YOLO vs VLM                                   │
│  └─ Apply plant health logic                                     │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    TIMESCALEDB STORAGE                           │
│  plant_snapshots (extended)                                      │
│  ├─ vlm_summary (TEXT)                                           │
│  ├─ vlm_analysis (JSONB)                                         │
│  ├─ plant_health_guess (TEXT)                                    │
│  ├─ analysis_reliability (JSONB)                                 │
│  └─ analysis_status (TEXT)                                       │
│                                                                   │
│  video_analysis (new table)                                      │
│  ├─ event_type (TEXT)                                            │
│  ├─ vlm_analysis (JSONB)                                         │
│  └─ frame_paths (TEXT[])                                         │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                             │
│  app.py (extended)                                               │
│  ├─ GET /api/analysis/latest-image                               │
│  ├─ GET /api/analysis/latest-video                               │
│  ├─ GET /api/analysis/recent                                     │
│  ├─ GET /api/analysis/health-alerts                              │
│  └─ POST /api/analysis/run-latest                                │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                     REACT DASHBOARD                              │
│  ├─ AIAnalysisCard.jsx (image analysis)                          │
│  ├─ VideoAnalysisCard.jsx (video events)                         │
│  ├─ PlantHealthCard.jsx (health alerts)                          │
│  └─ AIStatusCard.jsx (processing status)                         │
└──────────────────────────────────────────────────────────────────┘
```

### **Module Structure**

```
plant-monitor/
├── backend/
│   ├── vlm/                          # VLM analysis module
│   │   ├── __init__.py               # Module exports
│   │   ├── ollama_client.py          # Ollama REST API wrapper
│   │   ├── vlm_analyzer.py           # Core VLM interface
│   │   ├── prompt_templates.py       # Structured prompts
│   │   ├── video_frame_sampler.py    # Frame extraction
│   │   └── analysis_rules.py         # Intelligent rules engine
│   │
│   ├── migrations/
│   │   └── 004_add_vlm_analysis.sql  # Database schema
│   │
│   ├── capture_with_vlm.py           # Complete pipeline
│   ├── app.py                        # FastAPI (to be extended)
│   ├── requirements.txt              # Dependencies
│   └── .env.example                  # Configuration
│
└── frontend/src/
    ├── AIAnalysisCard.jsx            # Image analysis UI
    ├── VideoAnalysisCard.jsx         # Video event UI
    ├── PlantHealthCard.jsx           # Health alerts UI
    └── AIStatusCard.jsx              # Processing status UI
```

---

## 🚀 Installation & Setup

### **Step 1: Install Ollama**

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

### **Step 2: Pull LLaVA Model**

```bash
# Pull 7B model (recommended - ~4GB download)
ollama pull llava:7b

# Alternative: 13B model (better accuracy, needs 16GB RAM)
# ollama pull llava:13b

# Verify model is available
ollama list
```

### **Step 3: Start Ollama Server**

```bash
# Start Ollama (runs on http://localhost:11434)
ollama serve

# Test with a simple query
ollama run llava:7b
```

### **Step 4: Install Python Dependencies**

```bash
cd plant-monitor/backend
source ../../.venv/bin/activate

# Add to requirements.txt:
# requests>=2.31.0
# Pillow>=10.0.0

pip install requests Pillow
```

### **Step 5: Run Database Migration**

```bash
# Run VLM schema migration
PGPASSWORD=plantpass psql -h localhost -p 5433 -U plantuser -d plantdb \
  -f migrations/004_add_vlm_analysis.sql

# Verify tables created
PGPASSWORD=plantpass psql -h localhost -p 5433 -U plantuser -d plantdb \
  -c "\d plant_snapshots" | grep vlm
```

### **Step 6: Configure Environment**

```bash
# Add to .env file
echo "OLLAMA_HOST=http://localhost:11434" >> .env
echo "OLLAMA_MODEL=llava:7b" >> .env
echo "OLLAMA_TIMEOUT=120" >> .env
```

---

## 📅 Implementation Roadmap

### **Phase 1: Foundation (Week 1) - CURRENT**

**Goal:** Get basic VLM analysis working

✅ **Completed:**
- [x] Install Ollama and pull LLaVA model
- [x] Create VLM module structure
- [x] Implement Ollama client wrapper
- [x] Design structured prompt templates
- [x] Create database schema migration
- [x] Build core VLM analyzer interface

🔄 **Next Steps:**
1. Test Ollama connection
2. Run first image analysis
3. Validate JSON parsing
4. Test database insertion

**Commands:**
```bash
# Test Ollama health
python3 -c "from vlm.ollama_client import get_ollama_client; print(get_ollama_client().check_health())"

# Test image analysis
python3 capture_with_vlm.py
```

---

### **Phase 2: Image Analysis Pipeline (Week 1-2)**

**Goal:** Integrate VLM with existing YOLO pipeline

**Tasks:**
1. ✅ Create `capture_with_vlm.py` integration script
2. ⏳ Extend FastAPI with VLM endpoints
3. ⏳ Test end-to-end image analysis
4. ⏳ Validate reliability rules
5. ⏳ Add error handling and retries

**Success Criteria:**
- Image captured → YOLO → VLM → Database (< 10 seconds)
- Structured JSON reliably parsed (>95% success rate)
- Reliability rules correctly flag poor quality images

**Testing:**
```bash
# Manual test
python3 capture_with_vlm.py

# Check database
psql -h localhost -p 5433 -U plantuser -d plantdb \
  -c "SELECT time, vlm_summary, analysis_status FROM plant_snapshots ORDER BY time DESC LIMIT 5;"
```

---

### **Phase 3: Video Analysis (Week 2)**

**Goal:** Add video event analysis

**Tasks:**
1. ⏳ Implement frame sampling (uniform distribution)
2. ⏳ Test multi-frame analysis
3. ⏳ Create video analysis database writer
4. ⏳ Add video analysis to pipeline
5. ⏳ Test with real 5-second clips

**Success Criteria:**
- 5 frames extracted from video
- Event summary generated
- Video analysis stored in `video_analysis` table

---

### **Phase 4: FastAPI Integration (Week 2-3)**

**Goal:** Expose VLM results via REST API

**Tasks:**
1. ⏳ Add `/api/analysis/latest-image` endpoint
2. ⏳ Add `/api/analysis/latest-video` endpoint
3. ⏳ Add `/api/analysis/recent` endpoint
4. ⏳ Add `/api/analysis/health-alerts` endpoint
5. ⏳ Add `/api/analysis/run-latest` trigger endpoint
6. ⏳ Test all endpoints with Postman/curl

**API Examples:**
```bash
# Get latest image analysis
curl http://localhost:8000/api/analysis/latest-image | jq

# Get health alerts
curl http://localhost:8000/api/analysis/health-alerts | jq

# Trigger analysis on latest snapshot
curl -X POST http://localhost:8000/api/analysis/run-latest
```

---

### **Phase 5: React Dashboard (Week 3)**

**Goal:** Display VLM analysis in UI

**Tasks:**
1. ⏳ Create `AIAnalysisCard.jsx` component
2. ⏳ Create `VideoAnalysisCard.jsx` component
3. ⏳ Create `PlantHealthCard.jsx` component
4. ⏳ Create `AIStatusCard.jsx` component
5. ⏳ Integrate with existing dashboard
6. ⏳ Add real-time polling
7. ⏳ Test UI responsiveness

**Success Criteria:**
- VLM summary displayed on dashboard
- Plant health alerts highlighted
- Video events shown with timestamps
- Processing status visible

---

### **Phase 6: Production Optimization (Week 4)**

**Goal:** Make system production-ready

**Tasks:**
1. ⏳ Add VLM analysis queue (avoid blocking)
2. ⏳ Implement retry logic for failed analyses
3. ⏳ Add performance monitoring
4. ⏳ Optimize prompt templates
5. ⏳ Add model switching capability
6. ⏳ Create admin dashboard for VLM status
7. ⏳ Write comprehensive tests

**Performance Targets:**
- Image analysis: < 5 seconds
- Video analysis: < 15 seconds
- Database query: < 100ms
- API response: < 200ms

---

## 📚 Module Documentation

### **vlm/ollama_client.py**

**Purpose:** REST API wrapper for Ollama

**Key Functions:**
```python
class OllamaClient:
    def generate(prompt: str, image_path: str) -> dict
    def chat(messages: list, image_path: str) -> dict
    def check_health() -> bool
    def pull_model(model: str) -> bool
```

**Usage:**
```python
from vlm.ollama_client import get_ollama_client

client = get_ollama_client()
if client.check_health():
    result = client.generate("Describe this image", "plant.jpg")
    print(result['response'])
```

---

### **vlm/prompt_templates.py**

**Purpose:** Structured prompts for reliable JSON output

**Templates:**
- `IMAGE_ANALYSIS_PROMPT` - Standard image analysis
- `VIDEO_ANALYSIS_PROMPT` - Video event analysis
- `PLANT_HEALTH_DETAILED_PROMPT` - Detailed plant health

**JSON Output Schema:**
```json
{
  "person_present": true,
  "person_count": 1,
  "plant_visible": true,
  "plant_occluded": false,
  "plant_health_guess": "healthy",
  "yellowing_visible": false,
  "drooping_visible": false,
  "wilting_visible": false,
  "image_quality": "good",
  "summary": "A person is standing near a healthy potted plant."
}
```

---

### **vlm/vlm_analyzer.py**

**Purpose:** High-level VLM analysis interface

**Key Functions:**
```python
def analyze_image_with_vlm(
    image_path: str,
    analysis_type: str = "standard",
    yolo_metadata: dict = None
) -> dict

def analyze_video_with_vlm(
    video_path: str,
    frame_count: int = 5,
    yolo_metadata: dict = None
) -> dict

def test_vlm_connection() -> bool
```

**Return Structure:**
```python
{
    "success": True,
    "analysis": {...},  # Parsed JSON
    "raw_response": "...",  # Raw VLM output
    "error": None,
    "timestamp": "2026-04-10T18:30:00Z",
    "model": "llava:7b",
    "analysis_type": "standard"
}
```

---

### **vlm/analysis_rules.py**

**Purpose:** Intelligent reasoning and reliability checks

**Key Functions:**
```python
def check_reliability(vlm_analysis: dict, yolo_metadata: dict) -> dict
def apply_analysis_rules(vlm_result: dict, yolo_metadata: dict, sensor_data: dict) -> dict
def should_skip_analysis(yolo_metadata: dict, previous_analysis: dict, time_since_last: int) -> dict
def get_analysis_summary(enhanced_analysis: dict) -> str
```

**Rules Implemented:**
1. ✅ Poor image quality → Low reliability
2. ✅ Person occludes plant → Skip plant health
3. ✅ YOLO/VLM disagreement → Medium confidence
4. ✅ Plant not visible → Warning
5. ✅ Temperature alert → High priority
6. ✅ Health issues detected → High priority

---

### **vlm/video_frame_sampler.py**

**Purpose:** Extract frames from video clips

**Key Functions:**
```python
def sample_video_frames(video_path: str, num_frames: int = 5, method: str = "uniform") -> list
def extract_keyframes(video_path: str, threshold: float = 30.0) -> list
def get_frame_at_timestamp(video_path: str, timestamp_ms: int) -> str
def cleanup_frames(video_path: str)
```

**Sampling Methods:**
- `uniform` - Evenly spaced frames
- `keyframes` - Scene change detection
- `adaptive` - Content-aware sampling (future)

---

## 🔌 API Reference

### **Image Analysis Endpoints**

#### `GET /api/analysis/latest-image`

Get latest image analysis with VLM results

**Response:**
```json
{
  "time": "2026-04-10T18:30:00Z",
  "image_path": "plant_20260410_183000.jpg",
  "image_url": "http://localhost:8000/images/plant_20260410_183000.jpg",
  "boxed_image_url": "http://localhost:8000/images/plant_20260410_183000_boxed.jpg",
  "temperature_c": 26.5,
  "humidity_pct": 55.2,
  "person_detected": false,
  "plant_visible": true,
  "plant_health_guess": "healthy",
  "vlm_summary": "Healthy potted plant with green leaves, no person in frame",
  "vlm_analysis": {
    "person_present": false,
    "plant_visible": true,
    "plant_health_guess": "healthy",
    "image_quality": "good"
  },
  "analysis_reliability": {
    "reliable": true,
    "confidence": "high",
    "warnings": []
  },
  "analysis_status": "completed"
}
```

#### `GET /api/analysis/recent?limit=10`

Get recent analyzed snapshots

#### `GET /api/analysis/health-alerts`

Get snapshots with plant health concerns

**Response:**
```json
[
  {
    "time": "2026-04-10T18:30:00Z",
    "image_url": "...",
    "plant_health_guess": "yellowing",
    "yellowing_visible": true,
    "vlm_summary": "Plant showing signs of yellowing on lower leaves",
    "recommendations": ["Check watering schedule", "Verify light exposure"]
  }
]
```

#### `POST /api/analysis/run-latest`

Trigger VLM analysis on most recent snapshot

---

### **Video Analysis Endpoints**

#### `GET /api/analysis/latest-video`

Get latest video event analysis

**Response:**
```json
{
  "time": "2026-04-10T18:30:00Z",
  "video_path": "plant_20260410_183000.mp4",
  "video_url": "http://localhost:8000/videos/plant_20260410_183000.mp4",
  "event_type": "person_interaction",
  "person_entered": true,
  "person_left": false,
  "plant_touched": false,
  "significant_motion": true,
  "vlm_summary": "Person entered frame and approached plant but did not touch it",
  "frames_analyzed": 5,
  "analysis_status": "completed"
}
```

---

## 🎨 React Components

### **AIAnalysisCard.jsx**

Displays latest image analysis with VLM results

**Features:**
- Image with YOLO boxes
- VLM summary
- Plant health indicators
- Reliability confidence
- Recommendations

**Props:**
```jsx
<AIAnalysisCard 
  refreshInterval={30000}  // 30 seconds
  showReliability={true}
  showRecommendations={true}
/>
```

---

### **VideoAnalysisCard.jsx**

Shows video event analysis

**Features:**
- Video player
- Event timeline
- Motion detection
- Person tracking
- Plant interaction alerts

---

### **PlantHealthCard.jsx**

Displays plant health alerts and trends

**Features:**
- Health status indicator
- Alert history
- Trend chart (yellowing/drooping over time)
- Actionable recommendations

---

### **AIStatusCard.jsx**

Shows VLM processing status

**Features:**
- Ollama connection status
- Model information
- Processing queue
- Recent analysis count
- Error log

---

## 🧪 Testing & Validation

### **Test 1: Ollama Connection**

```bash
python3 << 'EOF'
from vlm.ollama_client import get_ollama_client

client = get_ollama_client()
if client.check_health():
    print("✅ Ollama is running")
    print(f"   Model: {client.model}")
else:
    print("❌ Ollama not available")
EOF
```

### **Test 2: Image Analysis**

```bash
# Capture and analyze
python3 capture_with_vlm.py

# Check result
psql -h localhost -p 5433 -U plantuser -d plantdb -c \
  "SELECT vlm_summary, analysis_status FROM plant_snapshots ORDER BY time DESC LIMIT 1;"
```

### **Test 3: Video Analysis**

```bash
# Test frame extraction
python3 << 'EOF'
from vlm.video_frame_sampler import sample_video_frames

frames = sample_video_frames("path/to/video.mp4", num_frames=5)
print(f"Extracted {len(frames)} frames")
for f in frames:
    print(f"  {f}")
EOF
```

### **Test 4: Rules Engine**

```bash
python3 << 'EOF'
from vlm.analysis_rules import check_reliability

analysis = {
    "person_present": True,
    "plant_occluded": True,
    "image_quality": "poor"
}

reliability = check_reliability(analysis)
print(f"Reliable: {reliability['reliable']}")
print(f"Confidence: {reliability['confidence']}")
print(f"Reasons: {reliability['reasons']}")
EOF
```

---

## 🔧 Troubleshooting

### **Ollama Not Running**

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Check logs
tail -f ~/.ollama/logs/server.log
```

### **Model Not Found**

```bash
# List available models
ollama list

# Pull LLaVA if missing
ollama pull llava:7b
```

### **JSON Parsing Fails**

**Symptom:** VLM returns text but JSON parsing fails

**Solution:**
1. Check prompt template - ensure it requests JSON
2. Lower temperature (more deterministic): `temperature: 0.1`
3. Add explicit JSON format example in prompt
4. Use regex fallback in `parse_json_from_response()`

### **Slow Analysis (>30 seconds)**

**Solutions:**
1. Use smaller model: `llava:7b` instead of `llava:13b`
2. Increase timeout: `OLLAMA_TIMEOUT=180`
3. Reduce image size before sending
4. Check CPU/GPU usage

### **Database Insert Errors**

```bash
# Check if migration ran
psql -h localhost -p 5433 -U plantuser -d plantdb -c "\d plant_snapshots" | grep vlm

# Re-run migration if needed
psql -h localhost -p 5433 -U plantuser -d plantdb -f migrations/004_add_vlm_analysis.sql
```

---

## 🚀 Advanced Features

### **Swap to Different Model**

```bash
# Pull alternative model
ollama pull llava:13b

# Update .env
echo "OLLAMA_MODEL=llava:13b" >> .env

# Restart system - no code changes needed!
```

### **Custom Prompts**

```python
from vlm.prompt_templates import get_custom_prompt

prompt = get_custom_prompt(focus_areas=['plant_health', 'lighting'])
```

### **Batch Analysis**

```python
# Analyze multiple images
from vlm.vlm_analyzer import analyze_image_with_vlm

images = ["img1.jpg", "img2.jpg", "img3.jpg"]
results = [analyze_image_with_vlm(img) for img in images]
```

### **Model Comparison**

```bash
# Test different models
for model in llava:7b llava:13b llava:34b; do
    echo "Testing $model..."
    OLLAMA_MODEL=$model python3 capture_with_vlm.py
done
```

---

## 📊 Performance Benchmarks

**Expected Performance (MacBook Pro M1, 16GB RAM):**

| Operation | LLaVA 7B | LLaVA 13B | LLaVA 34B |
|-----------|----------|-----------|-----------|
| Image Analysis | 3-5s | 8-12s | 20-30s |
| Video Analysis (5 frames) | 10-15s | 30-45s | 90-120s |
| JSON Parsing | <100ms | <100ms | <100ms |
| Database Insert | <50ms | <50ms | <50ms |
| **Total Pipeline** | **~8s** | **~15s** | **~35s** |

---

## ✅ Success Checklist

- [ ] Ollama installed and running
- [ ] LLaVA model pulled
- [ ] Database migration completed
- [ ] VLM module tests passing
- [ ] Image analysis working end-to-end
- [ ] Video frame extraction working
- [ ] FastAPI endpoints added
- [ ] React components created
- [ ] Rules engine validated
- [ ] Production deployment tested

---

## 🎯 Next Steps

**Immediate (This Week):**
1. Install Ollama and test connection
2. Run first image analysis
3. Validate database schema
4. Test reliability rules

**Short-term (Next 2 Weeks):**
1. Complete FastAPI integration
2. Build React dashboard
3. Test video analysis
4. Deploy to production

**Long-term (Next Month):**
1. Add analysis queue
2. Implement model switching
3. Create admin dashboard
4. Optimize performance

---

**🎉 Your local AI reasoning layer is ready to build!**

Start with Phase 1 and work through the roadmap systematically. Each phase builds on the previous one, ensuring a stable, production-ready system.
