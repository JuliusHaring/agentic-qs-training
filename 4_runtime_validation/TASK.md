# Chapter 4 — Runtime Validation

**Scenario:** The harness handles a normal ticket, a lockout, and abuse/prompt-injection. Enforce boundaries so agents cannot resolve abuse, escalate from the reply step, or ship tiny replies.

**Your work:** Follow the `# TODO` comments — implement the guardrail functions, register them on the agents, and finish the pre-resolve gate. Orchestration already runs with allow-all stubs.

**Time:** ~25–30 min · `python -m 4_runtime_validation.task` · Solution: `loesung.py`
