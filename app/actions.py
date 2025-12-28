from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Alert, Comment, User
from datetime import datetime

async def execute_action(alert: Alert, action: str, user: User, session: AsyncSession):
    """
    Executes a response action on an alert.
    Returns a status message.
    """
    if action == "block_ip":
        # Mock Firewall Block
        # In a real app, this would call a firewall API (e.g., Palo Alto, AWS WAF)
        
        # Log the action as a system comment
        comment_content = f"SYSTEM ACTION: IP {alert.ip} has been blocked on the firewall by {user.full_name or user.email}."
        
        # Create comment
        # We need a system user or just attribute it to the user who triggered it?
        # Let's attribute to the user for now, but prefix with SYSTEM ACTION.
        new_comment = Comment(
            alert_id=alert.id,
            user_id=user.id,
            content=comment_content
        )
        session.add(new_comment)
        
        # Update alert status? Maybe not automatically, but we could.
        # Let's leave status as is, or maybe set to "Investigating" if new.
        
        return f"IP {alert.ip} blocked successfully."

    elif action == "enrich_now":
        # Manual trigger for enrichment (if we wanted to re-run it)
        return "Enrichment triggered (mock)."
        
    else:
        raise ValueError(f"Unknown action: {action}")
