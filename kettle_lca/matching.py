"""BOM 항목마다 Commons Merged 공정 후보를 고르고 이유를 남긴다."""

from __future__ import annotations

from dataclasses import dataclass

from kettle_lca.uslci_store import ProcessSummary


@dataclass(frozen=True)
class MatchRule:
    material: str
    require_any: tuple[str, ...]
    prefer_phrases: tuple[str, ...]
    reject_phrases: tuple[str, ...]
    rationale: str


# 이름 규칙. 재활용·열성형은 새 주전자의 기본 경로에서 빼되, 후보는 표에 남긴다.
MATCH_RULES: tuple[MatchRule, ...] = (
    MatchRule(
        "Stainless steel",
        ("stainless",),
        ("flat rolled", "stainless steel"),
        ("recycled", "scrap", "useeio"),
        "스테인리스 고철이 아닌 생산 공정을 우선한다.",
    ),
    MatchRule(
        "Brass",
        ("brass",),
        ("brass",),
        ("recycled",),
        "황동 생산 공정을 찾는다.",
    ),
    MatchRule(
        "Copper",
        ("copper",),
        ("copper cathode", "copper, "),
        ("recycled", "sulfate", "useeio", "bridge"),
        "황산구리나 금액 다리는 구리 금속이 아니다. 물리 단위공정이 없으면 계산하지 않는다.",
    ),
    MatchRule(
        "Polypropylene (PP)",
        ("polypropylene",),
        ("injection molding", "rigid polypropylene"),
        ("recycled", "thermoforming"),
        "주전자 플라스틱 몸체는 사출이 가깝다. 사출 공정이 버진 수지를 이미 투입하면 수지를 따로 더하지 않는다.",
    ),
    MatchRule(
        "Polyvinyl chloride (PVC)",
        ("polyvinyl chloride", "pvc"),
        ("suspension", "resin"),
        ("recycled", "landfill", "membrane", "roofing", "msw", "combustion", "useeio"),
        "수명 종료와 지붕재는 주전자 부품이 아니다. 서스펜션 등급 버진 수지를 고르고, 전선 압출 공정은 데이터에 없으면 빠졌다고 적는다.",
    ),
    MatchRule(
        "Nylon, grade unspecified",
        ("nylon", "polyamide"),
        ("nylon 6", "polyamide 6", "injection"),
        ("recycled", "nylon 6,6", "nylon 66", "useeio", "bridge"),
        "등급이 없어 나일론 6을 대리로 우선한다. 6,6만 있으면 그 사실을 이유에 남긴다.",
    ),
    MatchRule(
        "Polyoxymethylene (POM)",
        ("polyoxymethylene", "acetal", "pom"),
        ("polyoxymethylene", "acetal"),
        ("recycled",),
        "POM 또는 아세탈 공정을 찾는다.",
    ),
    MatchRule(
        "Polycarbonate (PC)",
        ("polycarbonate",),
        ("polycarbonate",),
        ("recycled", "useeio", "bridge"),
        "폴리카보네이트 공정을 찾는다.",
    ),
    MatchRule(
        "Acrylonitrile-butadiene-styrene (ABS)",
        ("acrylonitrile", "abs"),
        ("copolymer resin", "abs"),
        ("recycled", "useeio", "bridge"),
        "ABS 공정을 찾는다.",
    ),
    MatchRule(
        "Silicone",
        ("silicone", "siloxane"),
        ("silicone",),
        ("recycled",),
        "실리콘 공정을 찾는다.",
    ),
    MatchRule(
        "LDPE packaging foil",
        ("ldpe", "low density polyethylene", "low-density polyethylene"),
        ("low-density polyethylene, ldpe", "ldpe; virgin"),
        ("recycled", "lldpe", "pipe", "injection", "stretch"),
        "필름 가공 공정은 없고 LLDPE는 다른 중합체다. LDPE 버진 수지를 쓰고 포일 가공은 빠졌다고 적는다.",
    ),
    MatchRule(
        "Cardboard packaging",
        ("corrugated", "cardboard", "containerboard"),
        ("average production", "corrugated product"),
        ("combustion", "100% recycled", "landfill"),
        "소매 포장은 평균 골판지를 쓴다. 100% 재활용 골판지는 기본값에서 빼 두고 나중 비교 후보로 남긴다.",
    ),
)


@dataclass(frozen=True)
class CandidateScore:
    summary: ProcessSummary
    score: int
    rejected: bool
    reason: str


def _name_has_token(name: str, token: str) -> bool:
    """lldpe 안의 ldpe처럼 다른 물질 이름에 끼어 있는 토큰은 맞지 않는다."""
    if token == "ldpe":
        return "ldpe" in name.replace("lldpe", " ")
    if token == "abs":
        padded = f" {name} "
        return " abs " in padded or " abs;" in padded or " abs," in padded
    return token in name


def score_process(rule: MatchRule, summary: ProcessSummary) -> CandidateScore | None:
    name = summary.name.lower()
    if not any(_name_has_token(name, token) for token in rule.require_any):
        return None
    rejected = any(_name_has_token(name, token) for token in rule.reject_phrases)
    score = 0
    matched_preferences: list[str] = []
    for phrase in rule.prefer_phrases:
        if _name_has_token(name, phrase):
            score += 10
            matched_preferences.append(phrase)
    if "virgin" in name:
        score += 5
    if summary.process_type == "UNIT_PROCESS":
        score += 2
    if rejected:
        score -= 100
    reason = "선호 구문: " + (", ".join(matched_preferences) if matched_preferences else "없음")
    if rejected:
        reason += ". 제외 구문이 이름에 있다."
    return CandidateScore(summary, score, rejected, reason)


def rank_candidates(
    rule: MatchRule, summaries: list[ProcessSummary], limit: int = 8
) -> list[CandidateScore]:
    scored = [item for item in (score_process(rule, summary) for summary in summaries) if item]
    scored.sort(key=lambda item: (-item.score, item.summary.name))
    return scored[:limit]


def choose_match(rule: MatchRule, summaries: list[ProcessSummary]) -> CandidateScore | None:
    ranked = rank_candidates(rule, summaries, limit=30)
    for candidate in ranked:
        if not candidate.rejected and candidate.score > 0:
            return candidate
    for candidate in ranked:
        if not candidate.rejected:
            return candidate
    return None
