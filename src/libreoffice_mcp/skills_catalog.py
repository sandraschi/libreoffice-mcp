"""Bundled skill discovery for webapp Skills page."""

from __future__ import annotations

import re
from pathlib import Path

_SKILLS_ROOT = Path(__file__).resolve().parent / "skills"
_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---", re.S)


def list_bundled_skills() -> list[dict[str, str]]:
    skills: list[dict[str, str]] = []
    if not _SKILLS_ROOT.is_dir():
        return skills
    for skill_dir in sorted(_SKILLS_ROOT.iterdir()):
        if not skill_dir.is_dir():
            continue
        md = skill_dir / "SKILL.md"
        if not md.is_file():
            continue
        text = md.read_text(encoding="utf-8")
        name = skill_dir.name
        description = ""
        match = _FRONTMATTER.match(text)
        if match:
            block = match.group(1)
            for line in block.splitlines():
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip()
                elif line.startswith("description:"):
                    description = line.split(":", 1)[1].strip()
        skills.append(
            {
                "id": skill_dir.name,
                "name": name,
                "description": description,
                "uri": f"skill://{skill_dir.name}/SKILL.md",
                "path": str(md),
            }
        )
    return skills


def read_skill(skill_id: str) -> dict[str, str] | None:
    md = _SKILLS_ROOT / skill_id / "SKILL.md"
    if not md.is_file():
        return None
    for s in list_bundled_skills():
        if s["id"] == skill_id:
            return {**s, "content": md.read_text(encoding="utf-8")}
    return None
