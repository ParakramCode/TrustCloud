from trust_engine.orchestrator import TrustOrchestrator
from trust_engine.aggregator import trust_score
from schemas.signals import DEFAULT_SIGNALS

class TrustEngine:
    def __init__(self):
        self.orchestrator = TrustOrchestrator()

    def evaluate(self, text):
        raw_signals = self.orchestrator.run(text)

        # normalize schema
        full_signals = DEFAULT_SIGNALS.copy()
        full_signals.update(raw_signals)

        trust = trust_score(full_signals)

        if trust > 0.75:
            level = "HIGH"
        elif trust > 0.5:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "trust_score": trust,
            "trust_level": level,
            "signals": full_signals
        }
