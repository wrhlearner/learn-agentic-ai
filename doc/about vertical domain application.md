# Question asked to gpt-5

I want to use LLM to do tasks in a specific vertical domain, which uses its own terminologies and has its own workflows. How to make LLM talk and solve problems using context of this domain? For instance, I want the LLM to root cause some problems and give suggestions. The debugging process involves observing report metrics step by step and detect abnormal metrics. And the suggestions may include some variable settings, scripts using functions in current code base, etc.

### Goal
Make the model operate like a domain expert: read your reports step by step, detect abnormal metrics, pinpoint likely root causes, and propose actionable fixes (variable settings, scripts using your codebase APIs).
### What works best in practice
- **Tool-augmented agent + RAG + structured outputs**:
  - Tools fetch/parse metrics and logs, run anomaly detectors, search your codebase, and test fixes.
  - Retrieval gives the model the right domain context (terminology, workflows, playbooks).
  - The model emits a strict JSON report (schema‑constrained), not free text. You render it and optionally auto‑apply parts.
- Add fine‑tuning once you have a few thousand good traces.
### Minimal architecture
- **Domain corpus** (RAG):
  - Glossary/ontology of your terms, metric definitions, workflows, known RCA playbooks, past incidents, “knobs” with safe ranges, codebase API docs/snippets.
- **Tools** (functions the model can call):
  - `get_report(metric|category, scope, run_id)`
  - `get_timeseries(metric, scope[, baseline])`
  - `detect_anomaly(series, method, params)`
  - `code_search(query)` and `get_symbol(path, fn)` for suggesting scripts using current code
  - `propose_knob_change(name, value)`; `dry_run(script)`; `apply_change(change_id)` (gated)
- **Reasoning loop** (observe → test → suggest):
  - Start with high‑leverage categories; fetch metrics; run detectors; gather evidence; branch by findings; propose fixes; optionally test or simulate.
- **Output contract (JSON Schema)**:
  - Guarantees parseable, actionable results; easy to score; enforces domain vocabulary.
If you have an MCP server for your metrics (e.g., PDHI), expose the above tools there and register it so the agent queries ground‑truth instead of hallucinating.
### Output schema (sketch)
```json
{
  "type": "object",
  "required": ["task_id","scope","findings","anomalies","root_causes","suggestions","confidence"],
  "properties": {
    "task_id": { "type": "string" },
    "scope": { "type": "object", "required": ["design","run"], "properties": {
      "design": { "type": "string" }, "run": { "type": "string" }
    }},
    "findings": { "type": "array", "items": {
      "type": "object", "required": ["metric","value","baseline","status","evidence"],
      "properties": {
        "metric": { "type": "string" },
        "value": {}, "baseline": {}, "status": { "enum": ["normal","borderline","abnormal"] },
        "evidence": { "type": "string" }
      }
    }},
    "anomalies": { "type": "array", "items": {
      "type": "object", "required": ["metric","severity","reason"],
      "properties": { "metric": { "type": "string" }, "severity": { "enum": ["low","med","high","critical"] }, "reason": { "type": "string" } }
    }},
    "root_causes": { "type": "array", "items": {
      "type": "object", "required": ["hypothesis","support","confidence"],
      "properties": { "hypothesis": { "type": "string" }, "support": { "type": "string" }, "confidence": { "type": "number" } }
    }},
    "suggestions": { "type": "array", "items": {
      "type": "object", "required": ["type","action","justification"],
      "properties": {
        "type": { "enum": ["variable_setting","script","code_change"] },
        "action": { "type": "object" },
        "references": { "type": "array", "items": { "type": "object", "properties": {
          "path": { "type": "string" }, "function": { "type": "string" }, "signature": { "type": "string" }
        }}},
        "justification": { "type": "string" },
        "safety": { "type": "string" }
      }
    }},
    "confidence": { "type": "number" },
    "open_questions": { "type": "array", "items": { "type": "string" } }
  }
}
```
### Agent loop (concise Python sketch)
```python
from dataclasses import dataclass
from typing import List, Dict, Any
# Tool interfaces (implement with your PDHI/MCP or internal APIs)
def get_report(category: str, run: str) -> Dict[str, Any]: ...
def get_timeseries(metric: str, run: str, baseline: str|None=None) -> List[float]: ...
def detect_anomaly(series, method="zscore", **kw) -> Dict[str, Any]: ...
def code_search(query: str) -> List[Dict[str, str]]: ...
# LLM call with JSON-schema-constrained output (provider-specific)
def llm_structured(prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]: ...
CHECK_ORDER = [
  "LOG/process/runtime",
  "REPORT-TIMING/DRV/setup & hold timing",
  "REPORT-CONGESTION/DRC/TM layers congestion",
  "REPORT-UTILIZATION/DENSITY/utilization",
  "REPORT-POWER/power",
]
def collect_findings(run: str) -> Dict[str, Any]:
  findings, anomalies = [], []
  for key in CHECK_ORDER:
    cat, metric = key.split("/", 1)
    rpt = get_report(cat, run)
    val = rpt.get(metric)
    series = get_timeseries(metric, run, baseline="last_good")
    det = detect_anomaly(series, method="zscore", window=50, thresh=3.0)
    status = "abnormal" if det.get("is_anomaly") else "normal"
    findings.append({"metric": metric, "value": val, "baseline": det.get("baseline"), "status": status,
                     "evidence": det.get("explain", "")})
    if status == "abnormal":
      anomalies.append({"metric": metric, "severity": det.get("severity","med"),
                        "reason": det.get("explain","")})
  return {"findings": findings, "anomalies": anomalies}
def propose_suggestions(run: str, context_docs: str) -> Dict[str, Any]:
  obs = collect_findings(run)
  prompt = f"""
You are a domain expert. Using the observations below and the domain docs, hypothesize root causes and propose safe, actionable fixes.
Only use domain terminology; cite concrete metrics and ranges. If evidence is insufficient, say so and ask for the next report to fetch.
Observations:\n{obs}\nDocs:\n{context_docs}
When proposing scripts, reference existing functions (path, function, signature).
"""
  return llm_structured(prompt, schema=OUTPUT_SCHEMA)
# Example invocation
# docs = retrieve_docs(query=["timing", "congestion", "power"])  # RAG step
# report = propose_suggestions(run="run_2025_08_10_nightly", context_docs=docs)
```
### Anomaly detection that works
- Start simple rules: thresholds from your SLOs and “util jump” deltas.
- Add statistics per metric family:
  - Z-score/EWMA for runtime, power, utilization spikes.
  - STL or Prophet for seasonality.
  - Categorical drift for clock topology/sinks distributions.
- Encode “known bad patterns” as deterministic checks (e.g., “open net > 0 is critical”).
### Making it talk like your domain
- System prompt that enforces your vocabulary and banned terms.
- Canonical few-shot traces showing the stepwise inspection order and acceptable fixes.
- RAG that injects:
  - Metric definitions and how to interpret them.
  - Cookbook: “If congestion high on M3/M4 and timing regresses, consider X/Y.”
  - API docs for your codebase functions used in scripts.
### Enforcing structure and safety
- Use schema-constrained JSON output; validate; if invalid or missing evidence, auto-ask the model to repair.
- Require evidence links: each claim must reference a metric and value/range.
- Add “abstain” path when context is insufficient; force the agent to request the next report via tools.
- Gate any “apply” action behind dry-run and human approve.
### When to fine‑tune
- After you’ve logged a few thousand successful analyses and suggestions:
  - Fine‑tune on instruction traces that include tool calls, observations, final JSON outputs.
  - Evaluate on parse rate, anomaly recall/precision, suggestion acceptance, and time‑to‑mitigation.
### Optional: grammar-constrained answers
If you want a strict DSL response (e.g., a remediation plan language), decode with a grammar or output a JSON AST that you pretty‑print to your DSL. The rest of the stack stays the same.
### Want a ready starter?
I can scaffold:
- A JSON Schema (final report)
- Tool stubs for metrics, anomaly detection, and code search
- A retrieval index for your domain docs
- A minimal orchestrator that runs the loop and produces the structured root cause analysis
Tell me your metric sources, the preferred check order, and where your code APIs live; I’ll tailor the schema and stubs.