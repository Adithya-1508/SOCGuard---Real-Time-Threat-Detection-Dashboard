# app/detector.py
from sklearn.ensemble import IsolationForest
import numpy as np
import pandas as pd
from typing import Dict, Any
import asyncio

# Simple in-memory online buffer for feature vectors (for demo)
BUFF_MAX = 5000
_features = []
_model = None
_model_lock = asyncio.Lock()

def featurize(event: Dict) -> Dict:
    # simple features: count of numeric tokens in message, has_ip, length, user_present
    # Enhanced features for better anomaly detection
    msg = str(event.get("message") or "").lower()
    user = str(event.get("user") or "").lower()

    features = {
        "len": len(msg),
        "num_digits": sum(c.isdigit() for c in msg),
        "has_user": 1 if event.get("user") else 0,
        "has_ip": 1 if event.get("ip") else 0,
        # New Security Features
        "has_sql": 1 if any(x in msg for x in ["select", "union", "drop", "insert", "update", "--", "1=1"]) else 0,
        "has_script": 1 if "<script>" in msg or "javascript:" in msg else 0,
        "is_failure": 1 if any(x in msg for x in ["failed", "error", "denied", "unauthorized", "reject"]) else 0,
        "is_admin": 1 if user in ["admin", "root", "administrator"] else 0
    }
    return features

async def add_and_maybe_train(event: Dict):
    global _model
    feat = featurize(event)
    _features.append(list(feat.values()))
    if len(_features) > BUFF_MAX:
        _features.pop(0)

    # train first model when we have enough points
    async with _model_lock:
        if _model is None and len(_features) >= 200:
            X = np.array(_features)
            _model = IsolationForest(n_estimators=100, contamination=0.01, random_state=42)
            _model.fit(X)

async def score_event(event: Dict) -> float:
    """Return anomaly score: higher -> more anomalous (0..inf)."""
    feat = featurize(event)
    async with _model_lock:
        if _model is None:
            # cold-start: return low anomaly for now
            return 0.0
        import numpy as np
        X = np.array([list(feat.values())])
        # IsolationForest.score_samples returns log density; we invert to a 0..1-like severity
        score = _model.decision_function(X)[0]  # higher = normal; lower = anomaly
        # map to severity [0,1]
        severity = max(0.0, min(1.0, (0.0 - score) + 0.01))
        return float(severity)
