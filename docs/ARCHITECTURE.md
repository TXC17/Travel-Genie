# Travel Genie: Academic System Architecture & Mathematical Formulation

## 1. System Overview
Travel Genie is a constraint-aware, multi-objective travel itinerary optimization system designed for final-year Bachelor of Engineering evaluation in Artificial Intelligence & Data Science.

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

## 2. Core Mathematical Models

### 2.1 Multi-Criteria Decision Making (MCDM) Scoring
For candidate attraction $a \in \mathcal{A}_D$, month $M \in [1, 12]$, and user interest vector $\mathbf{v}_u$:
$$\text{Score}(a) = \frac{w_i S_{\text{interest}}(a) + w_p S_{\text{pop}}(a) + w_s S_{\text{season}}(a, M) + w_b S_{\text{budget}}(a) + w_r S_{\text{rating}}(a)}{w_i + w_p + w_s + w_b + w_r}$$
where $\sum w_k = 1.0$ and sub-scores are normalized to $[0.0, 1.0]$.

### 2.2 Adaptive Geographic K-Means Spatial Day Clustering
- Coordinate projection: $(\phi, \lambda) \implies \mathbb{R}^2$ or Haversine distance matrix.
- Objective:
  $$\arg\min_{\mathbf{S}} \sum_{i=1}^K \sum_{\mathbf{x} \in S_i} \|\mathbf{x} - \boldsymbol{\mu}_i\|^2$$
  where $K = \min(\text{SightseeingDays}, |\text{EligibleAttractions}|)$.
- Edge Case Guardrails:
  - If $|\text{Attractions}| < K$, $K$ dynamically reduces to $|\text{Attractions}|$.
  - Secondary rebalancing heuristic ensures each day cluster contains between $N_{\min}$ and $N_{\max}$ attractions without creating isolated outliers.

### 2.3 Combinatorial Route Optimization (Google OR-Tools TSP)
- Formulation: Graph $G = (V, E)$ where $V = \{0, 1, \dots, m\}$ with node $0$ representing the day's hub/hotel.
- Arc cost $C_{ij} = d_{\text{haversine}}(v_i, v_j) \times \text{SpeedFactor}(\text{Mode})$.
- Objective:
  $$\min \sum_{i} \sum_{j} C_{ij} x_{ij}$$
  subject to node degree conservation and sub-tour elimination.
- Efficiency Benchmark:
  $$\Delta_{\text{efficiency}} = \frac{D_{\text{unoptimized}} - D_{\text{optimized}}}{D_{\text{unoptimized}}} \times 100\%$$

### 2.4 Neuro-Symbolic Generative AI Layer
- Google Gemini (`GEMINI_MODEL`, e.g., `gemini-2.5-flash`) strictly serves as:
  1. Semantic Constraint Extractor (Translates unstructured queries into Pydantic schema).
  2. Optimization Explainer (Synthesizes natural language trade-off rationales on top of deterministic outputs).
- **The LLM never generates attraction coordinates, distances, or schedules independently.**

## 3. Map & Visualization Architecture
- Interactive map rendering is 100% powered by **Leaflet & OpenStreetMap**.
- Zero external billing or proprietary API keys required for map presentation.

## 4. Data Provenance, Verification & Classification Protocol
To preserve academic integrity and align with the project synopsis, all data points adhere to a three-tier classification:
- **Tier 1 (Factual / Verified)**: Geographic coordinates from OpenStreetMap nodes; monument tariffs from official Archaeological Survey of India (ASI) notifications / Forest Department orders; operating hours from ASI/KSTDC/GTDC official registries.
- **Tier 2 (Curated Empirical Baselines)**: Recommended visit durations ($T_{\text{visit}}$) based on site scale; monthly climate normals ($S_{\text{season}}$) based on India Meteorological Department (IMD) historical data.
- **Tier 3 (Heuristic / Computed Proxies)**: Crowd density index ($\text{CrowdScore}$) computed from seasonal demand, day-of-week factors, and popularity signals; transit cost projections based on regional rate matrices.

All database models and JSON seed records embed an explicit `provenance` metadata dictionary and `is_verified` flag.

