#!/usr/bin/env python3
"""Generate the profile language chart from six selected public GitHub repositories.

Uses GitHub's /languages endpoint (Linguist classification, bytes of code).
This does not measure professional experience or personal authorship per file.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

OWNER = "danmaciel"
REPOSITORIES = (
    "monorepo_sistema_todo_com_microservices",
    "agendador_app_monorepo",
    "api",
    "diagrama_arquitetura_escalavel_aws",
    "rate_limite_golang",
    "arquitetura_hexagonal",
)
OUTPUT = Path("assets/portfolio-languages.svg")
PALETTE = ("#58A6FF", "#3FB950", "#D2A8FF", "#F2CC60", "#FF7B72", "#79C0FF", "#8B949E")


def languages_for(repo: str, token: str) -> dict[str, int]:
    url = f"https://api.github.com/repos/{OWNER}/{repo}/languages"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "portfolio-language-chart",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urlopen(Request(url, headers=headers), timeout=20) as response:
            values = json.load(response)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Failed to fetch language totals for {repo}: {exc}") from exc
    if not isinstance(values, dict) or any(
        not isinstance(k, str) or not isinstance(v, int) or v < 0
        for k, v in values.items()
    ):
        raise ValueError(f"Invalid language response for {repo}")
    return values


def build_svg(totals: dict[str, int], date: str) -> str:
    ordered = sorted(
        ((name, size) for name, size in totals.items() if size > 0),
        key=lambda x: (-x[1], x[0]),
    )
    total_bytes = sum(size for _, size in ordered)
    if not total_bytes:
        raise ValueError("No recognized language bytes in selected repositories")

    top = ordered[:6]
    remaining = sum(size for _, size in ordered[6:])
    if remaining:
        top.append(("Outras", remaining))

    width, height = 680, 114 + len(top) * 29 + 48
    x0, chart_width = 24, width - 48
    y0 = 72
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Linguagens dos seis projetos em destaque</title>',
        '<desc id="desc">Proporção aproximada dos bytes de linguagens identificados pelo GitHub Linguist nos seis repositórios públicos selecionados; não representa experiência profissional.</desc>',
        f'<rect width="{width}" height="{height}" rx="14" fill="#0D1117"/>',
        '<text x="24" y="33" fill="#F0F6FC" font-size="18" font-family="Arial, sans-serif" font-weight="bold">Linguagens dos projetos em destaque</text>',
        f'<text x="24" y="53" fill="#8B949E" font-size="12" font-family="Arial, sans-serif">GitHub Linguist · 6 repositórios públicos · {escape(date)}</text>',
        f'<rect x="{x0}" y="{y0}" width="{chart_width}" height="14" rx="7" fill="#30363D"/>',
    ]
    xpos = x0
    for idx, (_, size) in enumerate(top):
        portion = chart_width * size / total_bytes
        # Narrow segments are still represented proportionally in the bar.
        parts.append(
            f'<rect x="{xpos:.2f}" y="{y0}" width="{portion:.2f}" height="14" fill="{PALETTE[idx]}"/>'
        )
        xpos += portion
    for idx, (language, size) in enumerate(top):
        row_y = 117 + idx * 29
        percentage = 100 * size / total_bytes
        parts.extend((
            f'<circle cx="32" cy="{row_y - 4}" r="5" fill="{PALETTE[idx]}"/>',
            f'<text x="48" y="{row_y}" fill="#E6EDF3" font-size="13" font-family="Arial, sans-serif">{escape(language)}</text>',
            f'<text x="{width - 24}" y="{row_y}" text-anchor="end" fill="#C9D1D9" font-size="13" font-family="Arial, sans-serif">{percentage:.1f}%</text>',
        ))
    parts.append(
        f'<text x="24" y="{height - 22}" fill="#8B949E" font-size="11" font-family="Arial, sans-serif">Distribuição de código, não nível de domínio · Fonte: GitHub API /languages</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> int:
    token = os.getenv("GH_TOKEN", "")
    totals: dict[str, int] = {}
    for repository in REPOSITORIES:
        data = languages_for(repository, token)
        for name, size in data.items():
            totals[name] = totals.get(name, 0) + size
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    svg = build_svg(totals, today)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"Chart updated: {OUTPUT}, {len(totals)} languages from {len(REPOSITORIES)} projects.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
