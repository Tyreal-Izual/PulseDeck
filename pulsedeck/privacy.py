"""Account collection is deliberately local-only in this release."""
ACCOUNT_NETWORK_ENABLED = False

def unavailable():
    return {"ok": True, "disabled": True, "local_only": True, "source": "codex",
            "reason": "Account network access is disabled; local usage remains available."}
