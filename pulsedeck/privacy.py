"""Local statistics, with an explicit read-only exception for Reset Credits."""
import os

ACCOUNT_NETWORK_ENABLED = False
RESET_CREDITS_NETWORK_ENABLED = os.environ.get("PULSEDECK_RESET_CREDITS_ONLINE", "1").strip().lower() in {"1", "true", "yes", "on"}

def unavailable():
    return {"ok": True, "disabled": True, "local_only": True, "source": "codex",
            "reason": "Account network access is disabled; local usage remains available."}
