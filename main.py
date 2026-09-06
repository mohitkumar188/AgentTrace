from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, Optional, List
import datetime
import sqlite3
import json

app = FastAPI(title="Agent Observability Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "traces.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                step_number INTEGER NOT NULL,
                step_name TEXT NOT NULL,
                step_type TEXT NOT NULL,
                inputs TEXT NOT NULL,
                original_inputs TEXT,
                output TEXT NOT NULL,
                latency_ms REAL NOT NULL,
                status TEXT NOT NULL,
                was_healed INTEGER DEFAULT 0,
                heal_notes TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        # Backward compatibility if column is missing
        cursor.execute("PRAGMA table_info(traces)")
        columns = [row[1] for row in cursor.fetchall()]
        if "original_inputs" not in columns:
            cursor.execute("ALTER TABLE traces ADD COLUMN original_inputs TEXT")
        conn.commit()

init_db()

class TraceItem(BaseModel):
    session_id: str
    step_number: int
    step_name: str
    step_type: str
    inputs: Dict[str, Any]
    original_inputs: Optional[Dict[str, Any]] = None
    output: Any
    latency_ms: float
    status: str
    was_healed: Optional[bool] = False
    heal_notes: Optional[str] = "None"
    timestamp: Optional[str] = None

@app.post("/api/v1/trace")
async def collect_trace(trace: TraceItem):
    ts = datetime.datetime.utcnow().isoformat()
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO traces (
                session_id, step_number, step_name, step_type, 
                inputs, original_inputs, output, latency_ms, status, was_healed, heal_notes, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trace.session_id,
            trace.step_number,
            trace.step_name,
            trace.step_type,
            json.dumps(trace.inputs),
            json.dumps(trace.original_inputs) if trace.original_inputs else None,
            json.dumps(trace.output) if not isinstance(trace.output, str) else trace.output,
            trace.latency_ms,
            trace.status,
            1 if trace.was_healed else 0,
            trace.heal_notes,
            ts
        ))
        conn.commit()
    return {"status": "recorded"}

@app.get("/api/v1/sessions")
async def get_sessions():
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM traces ORDER BY session_id, step_number ASC")
        rows = cursor.fetchall()
        
    sessions = {}
    for r in rows:
        item = dict(r)
        item["inputs"] = json.loads(item["inputs"])
        item["original_inputs"] = json.loads(item["original_inputs"]) if item.get("original_inputs") else None
        try:
            item["output"] = json.loads(item["output"])
        except Exception:
            pass
        item["was_healed"] = bool(item["was_healed"])
        
        sid = item["session_id"]
        if sid not in sessions:
            sessions[sid] = []
        sessions[sid].append(item)
        
    return {"total_sessions": len(sessions), "sessions": sessions}