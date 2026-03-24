# Farmer-First Pakistan Demo Explained

## Why This Document Exists

This explains the demo architecture, inputs, and guardrails in plain terms.

## Critical Status Disclaimer

The demo is a UX layer over stored simulation-trained artifacts. Final thesis evidence is sourced from completed frozen runs (`113` + `42`), and the demo itself is still not a field-validation substitute.

## What The Demo Demonstrates Well

- user-friendly translation of RL outputs into farmer-readable advice cards
- explicit budget and moisture guardrails
- baseline comparison framing
- local/offline runnable interface for defense demonstrations

## What The Demo Does Not Demonstrate

- real-field deployment performance
- irrigation-control completion as learned action
- finalized rice-wheat thesis evidence
- real-farm validation of the thesis conclusions

## Input/Output Logic (Simplified)

- user enters crop/stage/land/budget/context
- backend selects artifact profile and computes recommendation
- guardrails clamp unsafe or unrealistic advice
- response includes recommendation + warnings + baseline comparison

## Guardrails (Why They Matter)

Guardrails convert model outputs into safer UI recommendations by enforcing practical constraints (budget, moisture-risk patterns, and conservative response behavior under uncertainty).

## Correct Defense Positioning

Use this line:

"This demo proves practical explainability and guardrail-first delivery of simulator-trained policies. Final comparative claims come from frozen completed evidence packs, while real-world field validation remains future work."
