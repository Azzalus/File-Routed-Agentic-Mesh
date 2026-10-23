---
name: vocabulary
description: >-
  Controlled-vocabulary capture for FRAM. Use during and after grilling to record
  resolved terms as OKF knowledge entities, keep one canonical term per concept, and
  lint user-facing output with the deterministic conformance checker.
---

# vocabulary - Controlled Vocabulary and STE Consistency

Use this skill to capture resolved terms, keep one canonical term per concept, and
verify user-facing output. This skill owns the STE rules and the conformance checker.

## STE Consistency Rules

Apply these rules to user-facing output only. Internal agent communication
(`BLACKBOARD.md`, `mcp-scratchpad/` logs) is exempt.

1. Use one canonical term for one concept. Never use a rejected synonym.
2. Write one meaning per sentence. One sentence carries one instruction.
3. Use active voice. Put the actor before the verb.
4. Keep each sentence to twenty words or fewer.
5. List rejected synonyms as `_Avoid_` entries on the canonical term.

## Capture Rules

- **Be opinionated.** Give every concept one canonical term. List the rejected
  synonyms.
- **Define what it IS, not what it does.** State the concept, not its behaviour.
- **Capture project terms only.** Do not capture generic programming concepts.
- **No implementation details.** The definition states the concept, not the code.

## Precedence

A per-task term shadows the workspace term for that task only. Promote a task term
to the workspace catalog at Stage 04.

## Where Terms Live

| Scope | Path |
| :--- | :--- |
| Workspace | `knowledge/schemas/workspace-vocabulary.json` |
| Per-task | `active-tasks/<task>/knowledge/schemas/<task>-vocabulary.json` |

Both entities conform to `$schema: https://schema.okf.org/v1/knowledge.json`.

## Vocabulary Entity Shape

```json
{
  "$schema": "https://schema.okf.org/v1/knowledge.json",
  "metadata": {"id": "schema-workspace-vocabulary", "domain": "fram", "version": "1.0"},
  "type": "schema",
  "properties": {
    "name": "Workspace Vocabulary",
    "description": "Controlled vocabulary catalog.",
    "terms": [
      {"canonical": "frontier", "definition": "The set of open decisions.", "avoid": ["queue"], "source_task": "workspace"}
    ]
  },
  "relations": [],
  "invariants": ["inv-ste"]
}
```

## The Conformance Checker

Run the checker to verify output. The checker is deterministic and returns exit code
0 on PASS and 1 on FAIL.

```bash
# Contract self-test
uv run .agents/skills/vocabulary/scripts/conformance_checker.py --self-test

# Run the six negative fixtures
uv run .agents/skills/vocabulary/scripts/conformance_checker.py --mutation-test .agents/skills/vocabulary/fixtures

# Lint one artifact against the vocabulary
uv run .agents/skills/vocabulary/scripts/conformance_checker.py --lint --artifact <path> --vocabulary knowledge/schemas/workspace-vocabulary.json

# Lint the grilling log and assert the skill mandate
uv run .agents/skills/vocabulary/scripts/conformance_checker.py --lint --log active-tasks/<task>/mcp-scratchpad/grilling-log.json --mandate .agents/skills/grilling/SKILL.md

# Pre-existing mode: report but never fail
uv run .agents/skills/vocabulary/scripts/conformance_checker.py --preexisting --artifact query.md
```

The checker prints one `VIOLATION: <rule>` line per failure. A traceback is not a
detection.

## Language-Delimiter Map

Comments are allowed in all source files. Delimiter characters only delimit comments.
Comment content must not collide with the delimiter syntax. The checker strips
delimiters with a language map, then lints the inner text.
