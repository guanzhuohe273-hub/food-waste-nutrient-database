from __future__ import annotations
from dataclasses import dataclass, asdict
import re

TARGET_ALIASES = {
    "total dietary fibre": ["total dietary fibre", "total dietary fiber", "total fibre", "total fiber", "dietary fibre", "dietary fiber", "tdf", "总膳食纤维", "膳食纤维"],
    "soluble dietary fibre": ["soluble dietary fibre", "soluble dietary fiber", "sdf", "可溶性膳食纤维"],
    "protein recovery": ["protein recovery", "recovery of protein", "protein recovered", "protein-recovery", "蛋白回收"],
    "protein content": ["protein content", "protein concentration", "protein amount", "蛋白含量"],
    "protein": ["protein", "蛋白"],
    "total phenolic content": ["total phenolic content", "polyphenol", "polyphenols", "phenolic", "phenolics", "tpc", "总酚", "多酚"],
    "total flavonoid content": ["total flavonoid content", "flavonoid", "flavonoids", "tfc", "黄酮"],
    "pectin": ["pectin", "果胶"],
    "calcium": ["calcium", "ca", "钙"],
    "zinc": ["zinc", "zn", "锌"],
    "iron": ["iron", "fe", "铁"],
    "potassium": ["potassium", "k", "钾"],
    "selenium": ["selenium", "se", "硒"],
    "magnesium": ["magnesium", "mg", "镁"],
    "sodium": ["sodium", "na", "钠"],
}

MATERIAL_ALIASES = {
    "brewer's spent grain": ["brewer's spent grain", "brewers spent grain", "spent grain", "bsg"],
    "globe artichoke": ["globe artichoke", "artichoke"],
    "clementine": ["clementine"],
    "banana": ["banana", "香蕉"],
    "mango": ["mango", "芒果"],
    "papaya": ["papaya"],
    "apple": ["apple"],
    "pineapple": ["pineapple"],
    "cucumber": ["cucumber"],
    "lime": ["lime"],
    "lemon": ["lemon"],
    "orange": ["orange"],
    "guava": ["guava"],
    "kumquat": ["kumquat"],
    "watermelon": ["watermelon"],
    "passion fruit": ["passion fruit", "passion-fruit"],
}

FRACTION_ALIASES = {
    "peel": ["peel", "rind", "skin", "皮"],
    "leaf": ["leaf", "leaves"],
    "stem": ["stem", "stems"],
    "outer bract": ["outer bract", "outer bracts", "bract", "bracts"],
    "pomace": ["pomace"],
    "seed": ["seed", "seeds"],
    "seed kernel": ["seed kernel", "kernel"],
}

METHOD_ALIASES = {
    "freeze drying": ["freeze drying", "freeze-dried", "freeze dried", "lyophilization", "lyophilised", "lyophilized"],
    "ultrasound-assisted extraction": ["ultrasound-assisted extraction", "ultrasound", "ultrasonication", "uae"],
    "maceration": ["maceration", "macerated"],
}

BASIS_ALIASES = {
    "dried sample": ["dried sample", "dried samples"],
    "dry": ["dry basis", "dry matter", "dry sample"],
    "wet": ["wet basis", "fresh basis", "wet sample"],
}

COUNT_TERMS = ["how many", "number of", "count", "entries", "多少", "几条"]
RANK_TERMS = ["highest", "greatest", "maximum", "max", "most", "richest", "best", "top", "最高", "最多", "最丰富", "最佳"]
SOURCE_TERMS = ["source", "citation", "doi", "paper", "出处", "文献"]
COMPARE_TERMS = ["compare", "comparison", "versus", " vs ", "对比", "比较"]

@dataclass(frozen=True)
class SemanticFrame:
    original: str
    normalized: str
    targets: tuple[str, ...]
    materials: tuple[str, ...]
    fractions: tuple[str, ...]
    methods: tuple[str, ...]
    bases: tuple[str, ...]
    intent: str
    confidence: float

    def to_dict(self) -> dict:
        return asdict(self)


def _contains_alias(text: str, alias: str) -> bool:
    low = text.casefold()
    a = alias.casefold()
    if any(ord(ch) > 127 for ch in a):
        return a in low
    return re.search(rf"(?<!\w){re.escape(a)}(?!\w)", low) is not None


def _match_aliases(text: str, mapping: dict[str, list[str]]) -> list[str]:
    found: list[str] = []
    for canonical, aliases in mapping.items():
        for alias in sorted(aliases, key=len, reverse=True):
            if _contains_alias(text, alias):
                found.append(canonical)
                break
    return found


def normalize_question(question: str) -> SemanticFrame:
    q = " ".join(question.strip().split())
    targets = _match_aliases(q, TARGET_ALIASES)
    materials = _match_aliases(q, MATERIAL_ALIASES)
    fractions = _match_aliases(q, FRACTION_ALIASES)
    methods = _match_aliases(q, METHOD_ALIASES)
    bases = _match_aliases(q, BASIS_ALIASES)

    if "protein recovery" in targets or "protein content" in targets:
        targets = [x for x in targets if x != "protein"]
    if "soluble dietary fibre" in targets and "total dietary fibre" in targets:
        if "soluble" in q.casefold() or "可溶" in q:
            targets = [x for x in targets if x != "total dietary fibre"]

    low = q.casefold()
    if any(t in low for t in COUNT_TERMS) or any(t in q for t in ["多少", "几条"]):
        intent = "count"
    elif any(t in low for t in SOURCE_TERMS) or any(t in q for t in ["出处", "文献"]):
        intent = "source"
    elif any(t in low for t in COMPARE_TERMS) or any(t in q for t in ["对比", "比较"]):
        intent = "compare"
    elif any(t in low for t in RANK_TERMS) or any(t in q for t in ["最高", "最多", "最丰富", "最佳"]):
        intent = "rank"
    else:
        intent = "retrieve"

    normalized = q
    for mapping in (TARGET_ALIASES, MATERIAL_ALIASES, FRACTION_ALIASES, METHOD_ALIASES, BASIS_ALIASES):
        for canonical, aliases in mapping.items():
            for alias in sorted(aliases, key=len, reverse=True):
                if any(ord(ch) > 127 for ch in alias):
                    pattern = re.escape(alias)
                else:
                    pattern = rf"(?<!\w){re.escape(alias)}(?!\w)"
                normalized = re.sub(pattern, canonical, normalized, flags=re.IGNORECASE)

    signal_count = bool(targets) + bool(materials) + bool(fractions) + bool(methods) + bool(bases)
    confidence = min(1.0, 0.35 + 0.12 * signal_count + (0.18 if intent != "retrieve" else 0.0))
    return SemanticFrame(q, normalized, tuple(targets), tuple(materials), tuple(fractions), tuple(methods), tuple(bases), intent, confidence)
