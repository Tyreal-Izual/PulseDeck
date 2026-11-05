"""UI-independent module catalog; collection remains in the tested adapters."""
from dataclasses import asdict, dataclass

@dataclass(frozen=True)
class Module:
    id: str
    name: str
    reports: tuple[str, ...]
    data_kind: str
    refresh_seconds: int
    description: str

MODULES = (
    Module("codex", "Codex", ("local-usage",),
           "usage", 60, "Local token, model and session history. Account network queries are disabled."),
    Module("claude", "Claude Code", ("claude-usage",),
           "usage", 15, "Local token history and captured subscription quotas."),
    Module("isambard", "Isambard", ("isambard-status",),
           "service", 300, "Public service status and planned maintenance."),
    Module("radar", "Radar", (), "benchmark", 14400,
           "Community model assessment scores, with the source test period."),
)
SOURCE_IDS = frozenset(module.id for module in MODULES)

def describe(enabled: frozenset[str]) -> list[dict]:
    return [{**asdict(module), "enabled": module.id in enabled} for module in MODULES]
