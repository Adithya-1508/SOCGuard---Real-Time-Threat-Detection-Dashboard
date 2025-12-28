from pydantic import BaseModel, IPvAnyAddress, Field
from typing import Optional, Dict

class EventIn(BaseModel):
    source: str = Field(..., min_length=1, max_length=50, description="Source of the event (e.g. firewall, agent)")
    timestamp: Optional[str] = Field(None, max_length=50) # ISO format usually < 30 chars
    ip: Optional[IPvAnyAddress] = None
    user: Optional[str] = Field(None, max_length=50) # Reduced from 100
    message: Optional[str] = Field(None, max_length=1024, description="Raw log message or description") # Reduced from 4096
    metadata: Optional[Dict] = Field(default_factory=dict, description="Additional context")

class AlertOut(BaseModel):
    id: int
    created_at: str
    severity: float
    summary: str
    ip: Optional[str]
    details: Dict
    status: str
