# Conversation-Level Trust Analysis — Honest Evaluation

## Written for Parakram | February 2026

**Your question:** Should I build conversation-level epistemic trust analysis?

**My answer:** Yes — but a much smaller version than what you described.

Here is the full evaluation.

---

## 1. Research Validity

### Is this a real phenomenon?

**Yes.** Long-context epistemic degradation in LLMs is a documented, active research area.

Evidence:

- **"Lost in the Middle" (Liu et al., 2023)** showed LLMs ignore information placed in the middle of long contexts. This is a well-cited NeurIPS paper.
- **Hallucination rate correlates with context length.** Multiple studies (Ji et al., 2023; Zhang et al., 2023) show that as conversations get longer, LLMs produce more unsupported claims.
- **Contradiction accumulation is measurable.** In multi-turn dialogues, LLMs frequently contradict their earlier statements when the conversation exceeds ~8-10 turns.
- **Coherence drift** — the gradual shift from the original topic — is observable and quantifiable via embedding similarity.

### Is it publishable?

**Conditionally.** Here is where honesty matters:

| Aspect | Assessment |
|--------|-----------|
| Novel research direction? | No — the phenomenon is known. But **measuring it with a formal epistemic trust framework** is novel. Nobody has applied defeater epistemology to conversation-level degradation. |
| Publishable at a top venue? | No — not with heuristic validators. You would need model-based validators and a labeled dataset. |
| Publishable as a workshop paper? | Plausibly — if you frame it as "a measurement framework for epistemic decay," not "we discovered epistemic decay." |
| Valuable for a college project? | **Absolutely.** This elevates the project from "I built a scoring tool" to "I studied a phenomenon." |

### The honest framing

What you are proposing is not "discovering" that LLMs degrade over long conversations. What you are proposing is:

> "Building an **instrumented measurement framework** that can quantify the rate, nature, and patterns of epistemic degradation in multi-turn LLM conversations."

This is a tool paper, not a discovery paper. That is fine — tool papers are valuable. But know the difference.

### Verdict: ✅ Research-valid, with honest scoping.

---

## 2. Conceptual Soundness

### Is conversation trust fundamentally different from single-text trust?

**Yes, and this is the core intellectual challenge.**

Your current system treats each input as an independent observation:

```
text → [validators] → scores → aggregation → trust assessment
```

Conversation trust introduces **temporal dependencies** that break this model:

### 2.1 Context Entanglement

In a conversation, turn N's meaning depends on turns 1 through N-1. "It" refers to something from 3 turns ago. "As I mentioned" requires memory. Your validators currently have no access to prior context.

**Impact on your system:** Your coherence validator measures sentence-to-sentence similarity *within* a single text. In a conversation, coherence should measure consistency *across* turns. These are different measurement instruments.

### 2.2 Error Propagation

If the LLM hallucinates a fact in turn 3, and the user accepts it, subsequent turns build on that hallucination. The trust of turn 7 is not independent of the trust of turn 3.

**Impact on your system:** Your aggregator computes trust per-text. It has no mechanism for saying "turn 7 inherits risk from turn 3's detected hallucination."

### 2.3 Trust Inertia

If the first 5 turns are excellent, humans (and measurement systems) tend to extend that trust to turn 6 even if turn 6 is bad. This is a cognitive bias that your system must either model or acknowledge.

**Impact on your system:** Your system is bias-free (each evaluation is independent). For conversation mode, this is actually an advantage — you measure each turn without prior bias. But you should acknowledge that the *user's* perceived trust may diverge from the system's measured trust.

### 2.4 Compounding Hallucinations

An LLM may introduce a fabricated entity in turn 2, then reference it again in turns 5 and 8 as though it were established fact. By turn 8, the hallucination is entrenched.

**Impact on your system:** Your hallucination detector uses keyword heuristics. It cannot detect that "the Brennan-Okafor theorem" was fabricated 6 turns ago and is now being cited as established. This is a hard problem.

### 2.5 What is conceptually sound to build

Given your validator architecture, these are achievable:

| Measurement | Feasible? | Why |
|------------|-----------|-----|
| Per-turn trust scores plotted over turn index | ✅ Yes | Just run existing validators on each turn |
| Coherence between adjacent turns | ✅ Yes | Reuse embedding similarity on turn pairs |
| Contradiction across turns | ⚠️ Partial | Your contradiction validator is sentiment-based, not cross-document |
| Hallucination accumulation | ⚠️ Partial | Can detect keyword markers, but not cross-turn fabrication |
| Semantic drift | ✅ Yes | Embedding similarity of turn N vs turn 1 |
| Reasoning depth degradation | ✅ Yes | Run reasoning validator on each turn, plot trend |

### Verdict: ✅ Conceptually sound, with acknowledged limitations.

---

## 3. System Architecture Impact

### What actually needs to change

Here is the honest assessment, component by component:

### 3.1 Data Model Changes

**Current model:**
```
TrustRequest → { text: str, metadata: dict }
```

**Needed:**
```
ConversationRequest → { 
    messages: [{ role: str, content: str }],
    metadata: dict
}
```

**Effort:** Small. One new Pydantic model. ~30 lines.

### 3.2 Validator Changes

**Current:** `BaseValidator.run(self, text: str) → ValidatorOutput`

**Needed:** No change to the validator interface. Validators still process text. The conversation analyzer feeds them each turn (or window) as text.

**Why this matters:** Your validator architecture is already modular. You do NOT need to redesign validators. You need a new **orchestration layer** that decides what text to feed them.

**Effort:** Zero validator changes. ~100 lines of new orchestration code.

### 3.3 New Component: Conversation Analyzer

This is the only significant new code:

```python
class ConversationAnalyzer:
    """Runs trust evaluation across conversation turns."""
    
    def analyze(self, messages: list[dict]) -> ConversationTrustReport:
        # 1. Evaluate each LLM turn individually
        per_turn = [engine.evaluate(msg["content"]) for msg in messages if msg["role"] == "assistant"]
        
        # 2. Evaluate sliding windows (2-turn, 3-turn)
        windows = self._sliding_windows(messages, sizes=[2, 3])
        windowed = [engine.evaluate(window) for window in windows]
        
        # 3. Compute cross-turn metrics
        drift = self._semantic_drift(per_turn)
        
        return ConversationTrustReport(per_turn, windowed, drift)
```

**Effort:** ~200-300 lines. This is the main work.

### 3.4 Storage/ETL Changes

**Current:** One JSON per evaluation.
**Needed:** One JSON per conversation, containing ordered per-turn results.

**Effort:** Small. ~50 lines of schema changes.

### 3.5 API Changes

One new endpoint:

```
POST /v1/evaluate/conversation
Body: { messages: [...], metadata: {...} }
```

**Effort:** ~40 lines.

### 3.6 Total Architecture Impact

| Component | Changes | Lines of Code |
|-----------|---------|---------------|
| Request schema | New `ConversationRequest` model | ~30 |
| Response schema | New `ConversationTrustReport` model | ~60 |
| Conversation analyzer | New module | ~250 |
| API endpoint | One new route | ~40 |
| Flatten/ETL script | Update for new format | ~50 |
| Validators | **None** | 0 |
| Aggregator | **None** | 0 |
| **Total** | | **~430 lines** |

**This is not overengineered.** 430 lines of new code, zero changes to existing code. Your architecture already supports this because validators are decoupled from orchestration.

### Verdict: ✅ Architecturally clean. Additive, not invasive.

---

## 4. Analytics Value

### What new analytics become possible

| Metric | Signal or Noise? | Why |
|--------|-------------------|-----|
| **Trust decay curve** (trust vs turn index) | ✅ **Real signal** | Directly measures whether later turns score lower |
| **Contradiction density vs turn index** | ⚠️ Partial signal | Your contradiction detector is basic, but directionally useful |
| **Coherence drift** (similarity to turn 1) | ✅ **Real signal** | Embedding similarity is a reliable proxy for topic drift |
| **Hallucination marker accumulation** | ⚠️ Partial signal | Keyword-based, so it will miss subtle hallucinations but catch obvious ones |
| **Reasoning depth degradation** | ✅ **Real signal** | If reasoning markers decrease in later turns, that is measurable |
| **Confidence-correctness divergence** | ❌ **Cannot measure** | You have no ground truth for correctness. You can measure trust vs confidence divergence, but not correctness. |
| **Long-context fragility index** | ✅ Derivable | Composite metric: rate of trust decay × defeater activation rate |

### The key graph

The single most valuable output of this feature is:

```
Trust Score
1.0 ┤
    │  ●━━●
    │       ╲
0.5 ┤         ●━━●
    │              ╲━━●
    │                   ╲━●━━●
0.0 ┤───────────────────────────→
    1   2   3   4   5   6   7   Turn
```

If you can produce this graph across 10+ conversations, and the downward trend is statistically significant (not just one cherry-picked example), that is a genuinely publishable result.

### Verdict: ✅ High analytics value. The trust decay curve alone justifies the feature.

---

## 5. Risk Analysis

### I will be brutally honest here.

### 5.1 False Patterns

**Risk: HIGH.** With only ~10 conversations and keyword/heuristic validators, you will see patterns. Many will be noise.

**Mitigation:** Report effect sizes with confidence intervals. If the trust decay slope has a 95% CI that includes zero, say so. Do not cherry-pick the conversations that show decay.

### 5.2 Spurious Correlations

**Risk: MEDIUM.** Longer turns tend to be later turns. Later turns tend to be on more specific subtopics. You may mistake "the text got more specialised" for "the text got less trustworthy."

**Mitigation:** Control for text length. Normalise scores by turn length. Report both raw and normalised results.

### 5.3 Measurement Illusion

**Risk: HIGH.** Your validators are heuristic-based. When you say "hallucination risk = 0.7", you have not actually detected a hallucination. You have detected keyword patterns that correlate with hallucination. The difference matters.

**Mitigation:** Use precise language. Say "hallucination risk indicator" not "hallucination detected." Say "trust estimate" not "trustworthiness." Your current system already does this well with the `blind_spots` list — extend this practice to conversation analysis.

### 5.4 Epistemic Overclaiming

**Risk: THE BIGGEST RISK.** The temptation will be to write in your report: "We demonstrate that LLMs exhibit systematic epistemic degradation over long conversations." This would be overclaiming unless:

1. You tested >50 conversations (not 5)
2. The decay trend was statistically significant (p < 0.05)
3. You controlled for confounding variables (topic drift, length, specificity)
4. You validated your validators against human judgement

**What you CAN honestly say:**

> "We present a measurement framework for tracking epistemic quality indicators across multi-turn conversations. In our sample of N conversations, we observe [specific trends], which are consistent with [specific hypotheses] but would require larger-scale validation to confirm."

This is honest, defensible, and still impressive.

### 5.5 Goodharting

**Risk: LOW for a student project.** Goodhart's law ("when a measure becomes a target, it ceases to be a good measure") applies if someone optimises LLM outputs to score high on your system. At student scale, this is not a concern. But mention it as a known limitation.

### Verdict: ⚠️ Real risks, all manageable with honest reporting.

---

## 6. Strategic Value for a Student Project

### The decisive question

You are a college student. You have:
- Limited time (weeks, not months)
- Limited compute (local CPU/GPU)
- Limited credits (AWS free tier)
- A working system that already produces research results
- An upcoming submission deadline (presumably)

### My honest assessment

| Question | Answer |
|----------|--------|
| Is this worth building? | **Yes — if you build the small version** |
| Is it overengineering? | **The full spec you described is.** Sliding windows, memory contamination, reinforcement loops — that is PhD-level work. The core feature (per-turn evaluation + trend analysis) is not overengineering. |
| Will it distract from core research? | **Only if you scope it wrong.** |
| Does it increase project quality? | **Significantly.** It transforms "I built a tool" into "I used a tool to study a phenomenon." |
| Does it improve academic value? | **Yes.** The trust decay curve is a research result, not just a feature. |

### What to build (the scoped version)

**Build this (3-4 days):**

1. New endpoint: `POST /v1/evaluate/conversation`
2. Accept `{ messages: [...] }` with role/content pairs
3. For each assistant turn: run existing validators, store per-turn results
4. Compute: mean trust per turn index, semantic drift (embedding similarity of turn N to turn 1)
5. Return: ordered list of per-turn trust scores + drift metrics
6. Seed data: 10 multi-turn conversations (5 short: 3-5 turns, 5 long: 8-15 turns)
7. Analysis: One graph showing trust vs turn index, one showing semantic drift vs turn index

**Do NOT build this (save for future work):**

- Sliding window analysis (adds complexity, marginal insight)
- Memory contamination detection (requires cross-document NLI, which you don't have)
- Reinforcement loop detection (requires causal modeling)
- Confidence-correctness divergence (requires ground truth you lack)
- Custom conversation-aware validators (redesign work with unclear payoff)

### The 80/20 version

The per-turn evaluation with trend analysis gives you **80% of the research value with 20% of the work.** The remaining features are worth mentioning in your "Future Work" section but not worth building now.

### What your report can say after building this

> "TrustCloud AI includes a conversation-level analysis mode that tracks epistemic trust indicators across multi-turn LLM interactions. By evaluating each assistant turn independently using the same epistemic trust framework, we can observe trends in coherence, contradiction risk, hallucination risk, and reasoning depth as conversations progress. In our sample of N conversations, we observed [results], suggesting that [interpretation]. This framework provides a basis for systematic study of epistemic quality in long-context LLM interactions."

This is honest, impressive, and defensible.

---

## Summary Decision Matrix

| Evaluation Axis | Verdict | Confidence |
|-----------------|---------|------------|
| Research validity | ✅ Valid | High |
| Conceptual soundness | ✅ Sound (with limits) | High |
| Architecture impact | ✅ Clean (~430 LOC) | High |
| Analytics value | ✅ High | Medium-High |
| Risk level | ⚠️ Manageable | Medium |
| Strategic value | ✅ Worth it (scoped) | High |

### **Final recommendation: Build the scoped version. It takes 3-4 days and meaningfully elevates the project.**

---

## Appendix: What the Scoped Version Does NOT Require

These are explicitly out of scope for the student version:

- No new validators
- No aggregator changes 
- No database
- No new ML models
- No cross-document NLI
- No ground truth labeling
- No sliding windows
- No memory graph
- No causal modeling

If any mentor or reviewer suggests these, the answer is: "These are documented in our future work section. The current version establishes the measurement framework that these extensions would build upon."
