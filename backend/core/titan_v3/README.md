# 🧠 Module: TITAN v3 (The Brain)

**Version:** 3.0.0  
**Status:** ✅ Production-Ready  
**Last Updated:** January 31, 2026

---

## Purpose

TITAN v3 is the **AI Intelligence Core** of the entire system. It provides:
- **Natural Language Understanding** - Interprets user queries in plain English
- **Personality-Aware Responses** - Adapts tone based on query type and sentiment
- **GraphRAG Memory** - Builds knowledge graphs for deep reasoning
- **Self-Learning** - Evolves strategies based on interaction patterns
- **External Senses** - Pulls real-time data from BigQuery for context

---

## 📂 Architecture

```
backend/core/titan_v3/
├── README.md              # This file (Module Passport)
├── unified_engine.py      # ⭐ Main Orchestrator - process_query() entry point
├── personality_engine.py  # Tone & sentiment detection, mode selection
├── graph_rag.py           # Knowledge graph for deep reasoning
├── evolution_core.py      # Self-learning & strategy evolution
├── active_senses.py       # Real-time BigQuery data injection
└── phoenix_protocols.py   # Recovery & self-healing mechanisms
```

---

## 🔑 Key Components

### 1. `unified_engine.py` (The Orchestrator)
The main entry point for all AI queries. Coordinates all sub-modules.

**Key Class:** `TitanV3Engine`

**Key Method:**
```python
async def process_query(
    self,
    query: str,
    conversation_history: Optional[List[Dict]] = None,
    business_context: Optional[Dict] = None,
    use_pro_model: bool = False
) -> TitanResponse
```

**Pipeline Flow:**
1. Analyze user sentiment and query type (Personality Engine)
2. Build graph context for deep reasoning (GraphRAG)
3. Inject external data from BigQuery (Active Senses)
4. Apply learned strategies (Evolution Core)
5. Generate response with appropriate personality
6. Record interaction for learning

---

### 2. `personality_engine.py` (The Tone)
Detects user mood and selects appropriate response style.

**Key Class:** `PersonalityEngine`

**Modes:**
| Mode | Trigger | Style |
|------|---------|-------|
| `ADVISOR` | Business questions | Professional, data-driven |
| `ANALYST` | Data/metrics queries | Precise, numbered insights |
| `MENTOR` | Learning/how-to | Encouraging, step-by-step |
| `GUARDIAN` | Alerts/warnings | Urgent, action-oriented |

---

### 3. `graph_rag.py` (The Memory)
Builds knowledge graphs for context-aware reasoning.

**Key Class:** `GraphRAG`

**Capabilities:**
- Stores entity relationships (products, customers, trends)
- Enables multi-hop reasoning ("Why did cheesecake sales drop?")
- Persists learning across sessions

---

### 4. `active_senses.py` (The Eyes)
Fetches real-time business data to inject into AI context.

**Key Class:** `ActiveSenses`

**Data Sources:**
- Sales trends (last 7/30 days)
- Inventory levels
- Expense patterns
- Customer feedback

---

### 5. `evolution_core.py` (The Growth)
Self-learning system that improves over time.

**Key Class:** `EvolutionCore`

**Features:**
- Tracks successful response patterns
- Learns from user corrections
- Evolves strategies based on feedback

---

### 6. `phoenix_protocols.py` (The Healer)
Recovery and self-healing mechanisms.

**Key Class:** `PhoenixProtocols`

**Capabilities:**
- Graceful degradation on API failures
- Automatic retry with exponential backoff
- Fallback responses when AI is unavailable

---

## 🚀 API Endpoints

### Streaming Chat
```
POST /api/v1/chat/stream
```
**Headers:**
- `Content-Type: application/json`
- `Authorization: Bearer <token>` (optional)

**Body:**
```json
{
  "message": "What were my sales yesterday?"
}
```

**Response:** Server-Sent Events (SSE) stream

---

### Health Check
```
GET /api/v1/titan/v3/health
```

**Response:**
```json
{
  "status": "healthy",
  "engine": "titan_v3",
  "components": {
    "personality": "ok",
    "graph_rag": "ok",
    "active_senses": "ok",
    "evolution": "ok"
  }
}
```

---

## 🔧 Configuration

Uses centralized config from `pillars/config_vault.py`:
```python
from pillars.config_vault import get_bq_config

PROJECT_ID, DATASET_ID = get_bq_config()
```

**Environment Variables:**
- `GEMINI_API_KEY` - Google Gemini API key
- `PROJECT_ID` - BigQuery project ID
- `DATASET_ID` - BigQuery dataset name

---

## 🧪 Testing

The engine is tested via the Chat UI and API:
```bash
# Start backend
uvicorn api.main:app --port 8000

# Test streaming chat
curl -X POST "http://localhost:8000/api/v1/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello TITAN"}'
```

---

## 📚 Related Modules

- **Chat Router:** `api/routers/chat.py` - API endpoint wrapper
- **Gemini Chat:** `utils/gemini_chat.py` - Low-level Gemini integration
- **Config Vault:** `pillars/config_vault.py` - Centralized configuration

---

**Built with 🔥 by the TITAN Evolution Engine**
