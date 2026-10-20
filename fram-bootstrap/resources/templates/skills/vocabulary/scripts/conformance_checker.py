#!/usr/bin/env python3
"""
Conformance checker for the FRAM grilling/vocabulary suite.

Deterministic gate for AC4 (a)-(f). Returns exit code 0 on PASS, 1 on FAIL.
Prints a machine-readable `VIOLATION: <rule>` line for each failure so a caller
can classify the failure without parsing a traceback.

Modes:
    --self-test                     run internal unit checks (contract sanity)
    --mutation-test <fixtures-dir>  run the six AC4 negative fixtures
    --lint --artifact <path>        lint one user-facing artifact (AC4 a-c)
    --preexisting --artifact <path> lint in pre-existing mode (never fails; R33)

Options:
    --vocabulary <json>   vocabulary catalog (default: workspace entity)
    --log <json>          grilling log (AC4 d-f)
    --mandate <SKILL.md>  grilling skill body (asserts the log mandate; AC4 d-f)
    --report <json>       write a machine-readable report
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

STE_MAX_WORDS = 20

PASSIVE_VOICE = re.compile(
    r"\b(?:is|are|was|were|be|been|being)\s+(?:\w+ed|written|done|made|known|shown|given|taken)\b",
    re.IGNORECASE,
)

LANGUAGE_DELIMITERS = {
    ".py": ("#", None),
    ".sh": ("#", None),
    ".bash": ("#", None),
    ".yaml": ("#", None),
    ".yml": ("#", None),
    ".toml": ("#", None),
    ".ps1": ("#", None),
    ".rb": ("#", None),
    ".pl": ("#", None),
    ".r": ("#", None),
    ".js": ("//", ("/*", "*/")),
    ".jsx": ("//", ("/*", "*/")),
    ".ts": ("//", ("/*", "*/")),
    ".tsx": ("//", ("/*", "*/")),
    ".c": ("//", ("/*", "*/")),
    ".h": ("//", ("/*", "*/")),
    ".hpp": ("//", ("/*", "*/")),
    ".cpp": ("//", ("/*", "*/")),
    ".cc": ("//", ("/*", "*/")),
    ".java": ("//", ("/*", "*/")),
    ".cs": ("//", ("/*", "*/")),
    ".go": ("//", ("/*", "*/")),
    ".rs": ("//", ("/*", "*/")),
    ".swift": ("//", ("/*", "*/")),
    ".kt": ("//", ("/*", "*/")),
    ".css": (None, ("/*", "*/")),
    ".md": (None, ("<!--", "-->")),
    ".html": (None, ("<!--", "-->")),
    ".htm": (None, ("<!--", "-->")),
    ".xml": (None, ("<!--", "-->")),
    ".sql": ("--", ("/*", "*/")),
    ".lua": ("--", ("--[[", "]]")),
    ".hs": ("--", ("{-", "-}")),
}


class ConformanceError(Exception):
    """A single deterministic violation with a named rule."""

    def __init__(self, rule: str, detail: str):
        super().__init__(detail)
        self.rule = rule
        self.detail = detail


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def resolve_terms(vocabulary: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return the term list from catalog form (top-level) or OKF entity form."""
    terms = vocabulary.get("terms")
    if not terms:
        terms = (vocabulary.get("properties") or {}).get("terms") or []
    return terms


def canonical_terms(vocabulary: Dict[str, Any]) -> Tuple[set, Dict[str, str]]:
    """Return (canonical-term set lowercased, keep-case map)."""
    canon = {}
    for term in resolve_terms(vocabulary):
        name = str(term.get("canonical", "")).strip()
        if name:
            canon[name.lower()] = name
    return set(canon.keys()), canon


def avoid_synonyms(vocabulary: Dict[str, Any]) -> Dict[str, str]:
    """Return a map of rejected synonym (lowercased) -> canonical term."""
    synonyms = {}
    for term in resolve_terms(vocabulary):
        canonical = str(term.get("canonical", "")).strip()
        for bad in term.get("avoid", []) or []:
            synonyms[str(bad).strip().lower()] = canonical
    return synonyms


def sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def lint_text(
    text: str, vocabulary: Dict[str, Any], check_coverage: bool = True
) -> List[ConformanceError]:
    """AC4 (a), (b), (c) over one block of user-facing text."""
    errors = []
    canonical, keep_case = canonical_terms(vocabulary)
    avoid = avoid_synonyms(vocabulary)
    known = canonical | {v.lower() for v in avoid.values()}

    if check_coverage:
        for line in text.splitlines():
            if line.strip().startswith("#"):
                continue
            previous_end = 0
            for match in re.finditer(r"[A-Za-z_][A-Za-z0-9_-]{2,}", line):
                word = match.group(0)
                gap = line[previous_end:match.start()]
                previous_end = match.end()
                if match.start() == 0 or re.search(r"[.!?]\s*$", gap):
                    continue
                lowered = word.lower()
                if lowered in known or lowered in avoid:
                    continue
                if re.search(r"[A-Z]", word):
                    errors.append(
                        ConformanceError(
                            "AC4(a)-unknown-term",
                            f"term '{word}' is not in the resolved vocabulary",
                        )
                    )

    for sentence in sentences(text):
        words = re.findall(r"[A-Za-z_][A-Za-z0-9_-]*", sentence)
        for word in words:
            lowered = word.lower()
            if lowered in avoid:
                errors.append(
                    ConformanceError(
                        "AC4(b)-avoid-synonym",
                        f"avoided synonym '{word}' (use '{avoid[lowered]}')",
                    )
                )
        if len(words) > STE_MAX_WORDS:
            errors.append(
                ConformanceError(
                    "AC4(c)-ste-sentence-length",
                    f"sentence has {len(words)} words (max {STE_MAX_WORDS})",
                )
            )
        if PASSIVE_VOICE.search(sentence):
            errors.append(
                ConformanceError("AC4(c)-ste-passive-voice", f"passive voice in: {sentence}")
            )
    return errors


def extract_comments(path: Path) -> List[str]:
    """Strip delimiters using the language map, return comment inner text."""
    suffix = path.suffix.lower()
    line_delim, block = LANGUAGE_DELIMITERS.get(suffix, (None, None))
    text = path.read_text(encoding="utf-8", errors="ignore")
    found = []
    if block:
        start, end = block
        for match in re.finditer(re.escape(start) + r"(.*?)" + re.escape(end), text, re.DOTALL):
            found.append(match.group(1))
    if line_delim:
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(line_delim):
                found.append(stripped[len(line_delim):])
    return found


def check_log(log: Dict[str, Any], mandate_text: Optional[str]) -> List[ConformanceError]:
    """AC4 (d), (e), (f) over the grilling log and the skill mandate."""
    errors = []
    rounds = log.get("rounds", [])

    if not rounds:
        errors.append(
            ConformanceError("AC4(d)-round-before-finalize", "no round ran before finalization")
        )

    if len(rounds) > 2:
        errors.append(ConformanceError("AC4(d)-max-two-rounds", f"{len(rounds)} rounds ran (>2)"))

    for round_entry in rounds:
        for question in round_entry.get("questions", []):
            if question.get("has_manual_response") is not True:
                errors.append(
                    ConformanceError(
                        "AC4(e)-manual-response",
                        f"question '{question.get('id')}' has no manual-response option",
                    )
                )

    for drift in log.get("drift", []) or []:
        tier = drift.get("tier")
        response = drift.get("response")
        if tier not in ("minor", "structural"):
            errors.append(
                ConformanceError("AC4(f)-drift-tier", f"drift tier '{tier}' not declared")
            )
            continue
        if tier == "structural" and response != "halt":
            errors.append(
                ConformanceError(
                    "AC4(f)-structural-halt",
                    f"structural drift responded '{response}' instead of halt",
                )
            )
        if tier == "structural" and drift.get("user_explained") is not True:
            errors.append(
                ConformanceError(
                    "AC4(f)-structural-halt",
                    "structural drift without a user explanation",
                )
            )

    if mandate_text is not None:
        if "grilling-log.json" not in mandate_text:
            errors.append(
                ConformanceError("AC4(d)-log-mandate", "skill does not mandate the grilling log")
            )

    return errors


def run_self_test() -> int:
    """Exercise the checker contract on inline data. Exit 0 = pass."""
    vocabulary = {
        "terms": [
            {"canonical": "frontier", "avoid": ["queue", "backlog"]},
            {"canonical": "workspace", "avoid": ["repo-root"]},
        ]
    }
    good = "The frontier lists every open decision."
    bad = "The queue lists every open decision."
    assert not lint_text(good, vocabulary), "good sentence flagged"
    assert lint_text(bad, vocabulary), "avoided synonym not flagged"

    long_sentence = "This sentence deliberately contains far more than twenty words so that the checker must report a violation for exceeding the configured maximum length today"
    assert any(e.rule.endswith("sentence-length") for e in lint_text(long_sentence, vocabulary)), (
        "long sentence not flagged"
    )

    log_ok = {
        "rounds": [
            {
                "q_number": 1,
                "questions": [{"id": "Q1.1", "text": "x", "options": ["y"], "has_manual_response": True}],
            }
        ],
        "drift": [],
        "finalized_after_round": True,
    }
    assert not check_log(log_ok, None), "valid log flagged"

    log_structural = {
        "rounds": log_ok["rounds"],
        "drift": [
            {"tier": "structural", "detected_at_round": 1, "response": "q2", "user_explained": True}
        ],
        "finalized_after_round": True,
    }
    assert check_log(log_structural, None), "structural drift without halt not flagged"

    print("self-test: PASS")
    return 0


def run_mutation_test(fixtures_dir: Path) -> int:
    """Run the six AC4 negative fixtures. Exit 0 = pass."""
    mutations_path = fixtures_dir / "mutations.json"
    vocabulary = load_json(fixtures_dir / "vocabulary.json")
    good_artifact = (fixtures_dir / "artifact-good.md").read_text(encoding="utf-8")
    good_log = load_json(fixtures_dir / "grilling-log-good.json")
    mutations = load_json(mutations_path)

    failures = []
    for mutation in mutations.get("mutations", []):
        name = mutation["id"]
        expect_rule = mutation["rule"]
        kind = mutation["kind"]

        if kind == "artifact":
            errors = lint_text(mutation["text"], vocabulary)
        elif kind == "log":
            errors = check_log(mutation["log"], mutation.get("mandate_text"))
        else:
            failures.append(f"{name}: unknown fixture kind '{kind}'")
            continue

        rules = sorted({e.rule for e in errors})
        if not errors:
            failures.append(f"{name}: no violation detected")
            continue
        if expect_rule not in rules:
            failures.append(f"{name}: expected rule near '{expect_rule}', got {rules}")

    if failures:
        for failure in failures:
            print(f"VIOLATION: {failure}")
        return 1

    print(f"mutation-test: PASS ({len(mutations.get('mutations', []))} fixtures)")
    return 0


def run_lint(args) -> int:
    errors: List[ConformanceError] = []

    if args.artifact:
        artifact = Path(args.artifact)
        vocabulary = load_json(Path(args.vocabulary)) if args.vocabulary else {"terms": []}
        text = artifact.read_text(encoding="utf-8", errors="ignore")
        if artifact.suffix.lower() in LANGUAGE_DELIMITERS:
            for comment in extract_comments(artifact):
                errors.extend(lint_text(comment, vocabulary))
        errors.extend(lint_text(text, vocabulary))

    mandate_text = None
    if args.mandate:
        mandate_text = Path(args.mandate).read_text(encoding="utf-8", errors="ignore")

    if args.log:
        log = load_json(Path(args.log))
        errors.extend(check_log(log, mandate_text))

    report = {
        "status": "FAIL" if errors else "PASS",
        "violations": [{"rule": e.rule, "detail": e.detail} for e in errors],
    }

    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=2), encoding="utf-8")

    if not errors:
        print("lint: PASS")
        return 0

    for error in errors:
        print(f"VIOLATION: {error.rule} - {error.detail}")
    return 1


def run_preexisting(args) -> int:
    """R33: report pre-existing content but never fail the gate."""
    artifact = Path(args.artifact)
    vocabulary = load_json(Path(args.vocabulary)) if args.vocabulary else {"terms": []}
    text = artifact.read_text(encoding="utf-8", errors="ignore")
    errors = lint_text(text, vocabulary)

    report = {
        "status": "PREEXISTING",
        "baselined": True,
        "violations": [{"rule": e.rule, "detail": e.detail} for e in errors],
    }
    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"preexisting: {len(errors)} flagged (baselined, not a gate failure)")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="FRAM vocabulary conformance checker")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--mutation-test", metavar="FIXTURES_DIR")
    parser.add_argument("--lint", action="store_true")
    parser.add_argument("--preexisting", action="store_true")
    parser.add_argument("--artifact")
    parser.add_argument("--vocabulary")
    parser.add_argument("--log")
    parser.add_argument("--mandate")
    parser.add_argument("--report")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(run_self_test())
    if args.mutation_test:
        sys.exit(run_mutation_test(Path(args.mutation_test)))
    if args.preexisting:
        sys.exit(run_preexisting(args))
    if args.lint:
        sys.exit(run_lint(args))

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
