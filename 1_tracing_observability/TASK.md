# Chapter 1 — Tracing and Observability

**Scenario:** The helpdesk harness already processes tickets. Ops needs MLflow traces: one shared session, a parent span per ticket, child spans for triage/reply/resolve, and error status on failures.

**Your work:** Follow the `# TODO` comments — wrap the right steps in spans, attach a session, and surface useful inputs/outputs. Agents already run without tracing.

**Time:** ~25–30 min · `python -m 1_tracing_observability.task` · Solution: `loesung.py`
