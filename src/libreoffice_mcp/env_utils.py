"""Read/write .env for Settings page (fleet pattern)."""

from __future__ import annotations

from pathlib import Path

_SECRET_FRAGMENTS = (
    "SECRET",
    "PASSWORD",
    "TOKEN",
    "API_KEY",
    "PRIVATE",
    "OPENAI",
    "ANTHROPIC",
    "BEARER",
    "AUTH",
)


def repo_env_path() -> Path:
    return Path(__file__).resolve().parents[2] / ".env"


def read_env_file(path: Path | None = None) -> dict[str, str]:
    env_path = path or repo_env_path()
    if not env_path.is_file():
        return {}
    out: dict[str, str] = {}
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def redact_env(env: dict[str, str | None]) -> dict[str, str | None]:
    masked: dict[str, str | None] = {}
    for key, val in env.items():
        if val is None:
            masked[key] = None
            continue
        ku = key.upper()
        sensitive = any(s in ku for s in _SECRET_FRAGMENTS) or ku.endswith(("_KEY", "_TOKEN"))
        sv = str(val).strip()
        if sensitive or sv.startswith(("sk-", "sk_", "Bearer ")):
            masked[key] = "***REDACTED***"
        else:
            masked[key] = val
    return masked


def write_env_updates(updates: dict[str, str | None], path: Path | None = None) -> None:
    env_path = path or repo_env_path()
    existing = read_env_file(env_path)
    for key, value in updates.items():
        if value is None:
            existing.pop(key, None)
        else:
            existing[key] = str(value)
    lines: list[str] = []
    for key in sorted(existing.keys()):
        val = existing[key]
        if " " in val or "#" in val:
            val = f'"{val}"'
        lines.append(f"{key}={val}")
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
