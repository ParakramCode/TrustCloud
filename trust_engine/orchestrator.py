from validators.coherence import check_coherence
from validators.contradiction import check_contradiction
from validators.hallucination import check_hallucination
from validators.reasoning import check_reasoning_depth
from validators.factuality import check_factual_density
from validators.semantic import check_semantic_consistency

class TrustOrchestrator:
    def run(self, text):
        signals = {}

        signals["coherence"] = check_coherence(text)
        signals["contradiction"] = check_contradiction(text)
        signals["hallucination_risk"] = check_hallucination(text)
        signals["reasoning_depth"] = check_reasoning_depth(text)
        signals["factual_density"] = check_factual_density(text)
        signals["semantic_consistency"] = check_semantic_consistency(text)

        return signals
