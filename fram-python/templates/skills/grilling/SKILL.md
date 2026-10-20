---
name: grilling
description: >-
  Relentless design interview for FRAM Stage 01. Use before a plan is finalized to
  expose every open decision, ask the whole frontier in one question-tool round, and
  halt when ambiguity survives two rounds. Pairs with the vocabulary skill for term
  capture.
---

# grilling - Relentless Design Interview

Use this skill to clarify a plan or design **before** Stage 01 finalization. The
skill asks the user decisions; the agent looks up everything else itself.

## When to Run

Run the grilling phase at Stage 01, after reconnaissance and before the plan is
finalized. Do not act on an unsettled plan.

## The Design Tree and the Frontier

- Every design has decisions. A **decision** is a question with more than one
  defensible answer.
- Decisions depend on other decisions. The **frontier** is every decision whose
  prerequisites are already settled.
- The frontier grows as the user answers. Ask the whole frontier at once.

## Fact-Finding Is the Agent's Job

- Look up any fact you can obtain from the filesystem, the tools, or the web.
- Only put **decisions** to the user. Never ask the user for a fact you can obtain.
- An unsettled fact blocks only its downstream questions. Ask the rest of the
  frontier now.

## Rounds (Q1 and Q2)

- **Q1**: ask the whole frontier in one `question`-tool call. Number the questions
  `Q1.1`, `Q1.2`, and so on. Give every question a recommended answer, worded so
  that "yes" accepts it. Give every question a manual-response option so the user
  can type their own answer.
- **Q2**: run at most one clarification round, and only when an answer to Q1 is
  ambiguous. Ask only the ambiguous questions.
- If ambiguity survives Q2, **halt and return to the user**. Never proceed on an
  unconfirmed assumption.

## Drift Detection

- **Drift** is an explicit contradiction of a prior decision.
- **Minor drift** (for example, a reversed micro-instruction) may consume the Q2
  slot.
- **Structural drift** (a contradiction of fundamental design intent or safety
  posture) requires a dedicated drift response: state the conflict, require the
  user to explain their intention, and halt until they do.
- Drift never creates a Q3. Declare the drift tier when you detect drift.

## Mandated Log

Write the round to `active-tasks/<task>/mcp-scratchpad/grilling-log.json`. Conform
to this schema:

```json
{
  "rounds": [
    {
      "q_number": 1,
      "questions": [
        {
          "id": "Q1.1",
          "text": "the question text",
          "options": ["recommended answer", "alternative answer"],
          "has_manual_response": true
        }
      ]
    }
  ],
  "drift": [
    {
      "tier": "minor",
      "detected_at_round": 1,
      "response": "q2",
      "user_explained": false
    }
  ],
  "finalized_after_round": true
}
```

- At most two rounds. The `drift` tier is `minor` or `structural`.
- A structural-tier entry must have `response` set to `halt`.
- The log is internal agent communication, so STE wording rules do not apply to it.

## Do Not Act Until Confirmed

Stop after the rounds. Present shared understanding. Wait for the user to confirm.
Only then hand control back to Stage 01 finalization.

## Knowledge Capture

When the user resolves a term, write it with the **vocabulary** skill. The
grilling round produces the decisions; the vocabulary skill records the terms in the
OKF catalog.
