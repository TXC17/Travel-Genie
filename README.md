# Travel Genie: An AI-Driven System for Optimized Travel Itinerary Generation

[![Project Status: Phase 1 Active](https://img.shields.io/badge/Project%20Status-Phase%201%20Initialized-blue.svg)](#development-phases)
[![Architecture: Clean Layered](https://img.shields.io/badge/Architecture-Clean%20Layered-success.svg)](#system-architecture)
[![License: Academic Major Project](https://img.shields.io/badge/License-Academic%20Major%20Project-purple.svg)](#)

> **Final-Year Academic Major Project in Artificial Intelligence & Data Science**  
> An intelligent, constraint-aware travel decision-support system synthesizing Multi-Criteria Decision Making (MCDM), Geographic K-Means Clustering, Google OR-Tools Combinatorial Route Optimization (TSP), Heuristic Temporal & Budget Pruning, and Neuro-Symbolic Generative AI Explanations.

---

## 🌟 Key Innovations & Mathematical Core

1. **Explainable Multi-Criteria Recommendation Engine (MCDM)**: Weighted multi-attribute ranking evaluating cosine interest similarity, climate suitability matrices, historical popularity, and budget affordability.
2. **Adaptive Geographic K-Means Clustering**: Partitions top candidate attractions into $K \le \min(\text{Days}, |\text{Attractions}|)$ spatially compact day clusters using spherical/Haversine coordinate projections.
3. **Google OR-Tools Route Optimization (TSP)**: Combinatorial sub-tour minimization delivering verified travel distance reduction ($\Delta_{\text{distance}}$) and optimal visiting sequences.
4. **Temporal Slack & Budget Feasibility Engine**: Strict enforcement of daily sightseeing duration thresholds ($H_{\text{daily}}$), travel times, and Pareto cost-pruning heuristics.
5. **Neuro-Symbolic Conversational AI Layer**: Powered by Google Gemini (configurable model via `GEMINI_MODEL`, e.g. `gemini-2.5-flash`), strictly bounded to Natural Language Understanding (extracting Pydantic constraints) and Natural Language Explanation (synthesizing trade-off narratives). **The LLM never hallucinates coordinates or schedules.**
6. **Zero-Billing Map Visualization**: Built on **Leaflet & OpenStreetMap**, rendering cluster markers, interactive route polylines, and timeline steps without paid API dependencies.

---

## 🏗️ System Architecture

```
                                    +------------------------------------------+
                                    |        Frontend: React 18 + TS + Vite    |
                                    |     (Leaflet Map, Day Timelines, Chat)   |
                                    +--------------------+---------------------+
                                                         | REST / JSON
                                                         v
                                    +------------------------------------------+
                                    |        FastAPI Backend (API Gateway)     |
                                    +--------------------+---------------------+
                                                         |
         +--------------------+--------------------------+-------------------------+--------------------+
         |                    |                          |                         |                    |
         v                    v                          v                         v                    v
+------------------+ +------------------+     +--------------------+     +------------------+ +------------------+
|  MCDM Scorer     | | K-Means Spatial  |     | OR-Tools Route     |     | Duration & Budget| | Gemini AI Layer  |
|  (Recommender)   | | Clusterer (Days) |     | Optimizer (TSP)    |     | Pruner / Validator| (NLU + Explain)   |
+------------------+ +------------------+     +--------------------+     +------------------+ +------------------+
         |                    |                          |                         |                    |
         +--------------------+--------------------------+-------------------------+--------------------+
                                                         |
                                                         v
                                    +------------------------------------------+
                                    |     Persistence: PostgreSQL / SQLite     |
                                    |  (Dandeli, Coorg, Hampi, Goa Knowledge)  |
                                    +------------------------------------------+
```

---

## 🚀 Quickstart & Setup

### Prerequisites
- **Python 3.11+**
- **Docker & Docker Compose** (Optional for containerized execution)
- **Node.js 18+** (For frontend development)

### Local Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database seed & start backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
API Documentation: `http://localhost:8000/docs`

### Local Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install packages & launch dev server
npm install
npm run dev
```
Web Interface: `http://localhost:5173`

---

## 📊 Development Phases

- [x] **Phase 0**: Requirement Analysis, System Architecture, Algorithmic & DB Design
- [x] **Phase 1**: Repository, Docker, Backend Skeleton, Frontend Skeleton & Project Config
- [ ] **Phase 2**: Database Models, Migration & Curated Seed Datasets (Dandeli, Coorg, Hampi, Goa)
- [ ] **Phase 3**: User Authentication & Trip Preference APIs
- [ ] **Phase 4**: Explainable MCDM Recommendation Engine & Seasonal Analysis
- [ ] **Phase 5**: Geographic K-Means Spatial Clustering Engine
- [ ] **Phase 6**: Google OR-Tools Combinatorial Route Optimizer (TSP)
- [ ] **Phase 7**: Travel Duration, Temporal Slack & Budget Pruner
- [ ] **Phase 8**: Unified Itinerary Generation Pipeline & Academic Metrics
- [ ] **Phase 9**: React Interactive Itinerary UI, Leaflet Maps & Timelines
- [ ] **Phase 10**: Conversational AI & Neuro-Symbolic Explanation Layer
- [ ] **Phase 11**: Smart Replanning & Multi-User Collaboration
- [ ] **Phase 12**: Automated Test Suite & Stress Testing
- [ ] **Phase 13**: Final Academic Documentation & Viva Demonstration Readiness
