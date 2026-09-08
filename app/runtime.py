from dataclasses import dataclass

from app.services.policy_explainer import PolicyExplainer
from app.services.policy_indexer import PolicyIndexer
from app.services.policy_intelligence import PolicyIntelligence


@dataclass
class Runtime:
    indexer: PolicyIndexer | None = None
    explainer: PolicyExplainer | None = None
    intelligence: PolicyIntelligence | None = None


runtime = Runtime()
