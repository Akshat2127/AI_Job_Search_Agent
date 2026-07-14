# Product Requirements

## Product outcome

JobAgent AI helps multiple candidates manage a high-quality, human-approved job search. Gurbani Sharma is the first configured candidate; Akshat Sharma is a future candidate. Candidate facts must come from reviewed profile or resume data and must never be fabricated.

## Core journey

The user signs in, selects an owned candidate, reviews structured profile facts and preferences, configures authorized sources, ingests and deduplicates jobs, reviews deterministic eligibility and explainable fit analysis, makes a decision, generates grounded materials, opens the official application, optionally uses a safe form-filling assistant, explicitly performs final submission, and tracks outcomes and follow-ups.

## Safety invariants

- One explicit human approval checkpoint per application submission.
- No CAPTCHA/access-control bypass or prohibited LinkedIn/Indeed automation.
- No inferred sensitive/legal application answers.
- Every job retains source provenance; merges retain all aliases.
- Generated claims cite supporting candidate facts and job requirements.
- Database is the source of truth; exports and Sheets are secondary views.

## Initial success criteria

A clean local install can create a candidate, ingest from one public ATS connector, deduplicate and prefilter jobs, use a deterministic/fake fit provider, review decisions in the UI, generate grounded artifacts, export a resume, track an application, run a safe local browser dry run, inspect analytics, and pass all documented checks. Credential-gated functionality must fail clearly and remain disabled by default.

