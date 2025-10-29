"""Entity type classification for GEO Knowledge Graph."""

import re
from typing import Optional


class EntityTypeClassifier:
    """Classify entities into types based on heuristics."""
    
    def classify(self, entity_id: str, context: dict) -> str:
        """
        Classify an entity into a type.
        
        Types: Paper, Person, Organization, Concept, Topic, Event, Location, Other
        """
        eid = str(entity_id).lower()
        
        # arXiv papers
        if "arxiv.org" in eid or "/abs/" in eid:
            return "Paper"
        
        # DOI patterns
        if "doi.org" in eid or eid.startswith("10."):
            return "Paper"
        
        # URLs - check domain patterns
        if "://" in eid:
            if any(domain in eid for domain in [".edu", ".ac.", "university", "institute"]):
                return "Organization"
            if any(domain in eid for domain in ["github.com", "gitlab.com"]):
                return "Project"
            # Default for URLs
            return "WebResource"
        
        # Check context predicates
        predicates = context.get("predicates", [])
        if "authors" in predicates or "author" in predicates:
            return "Paper"
        if "employee" in predicates or "member" in predicates:
            return "Organization"
        
        # Name patterns (heuristic: contains spaces, capitalized words)
        if re.match(r"^[A-Z][a-z]+ [A-Z]", eid):
            return "Person"
        
        # Technical terms (lowercase, underscores, hyphens)
        if re.match(r"^[a-z_-]+$", eid):
            return "Concept"
        
        return "Other"


def infer_entity_type_from_predicates(subject: str, predicates: list) -> Optional[str]:
    """Infer entity type from the predicates used with it."""
    pred_set = {p.lower() for p in predicates}
    
    if {"authors", "title", "abstract", "categories"} & pred_set:
        return "Paper"
    if {"name", "affiliation", "email"} & pred_set:
        return "Person"
    if {"headquarter", "founded", "employees"} & pred_set:
        return "Organization"
    
    return None


# Global instance
classifier = EntityTypeClassifier()
