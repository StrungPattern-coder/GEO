from typing import Any, Dict, List
from dataclasses import dataclass
from ..config import settings

@dataclass
class Node:
    id: str
    labels: List[str]
    props: Dict[str, Any]

@dataclass
class Relation:
    start_id: str
    end_id: str
    type: str
    props: Dict[str, Any]


class GraphClient:
    def __init__(self):
        self._use_memory = False
        self._mem_facts: List[Dict[str, Any]] = []
        self._aliases: Dict[str, str] = {}
        try:
            from neo4j import GraphDatabase  # type: ignore
            self._driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )
            with self._driver.session() as s:
                s.run("RETURN 1")
        except Exception:
            self._use_memory = True
            self._driver = None  # type: ignore

    def _canonicalize_id(self, val: Any) -> Any:
        if not isinstance(val, str):
            return val
        s = val.strip()
        if not s:
            return s
        try:
            from urllib.parse import urlparse, urlunparse
            import re as _re
            u = urlparse(s)
            if u.scheme and u.netloc:
                scheme = 'https' if u.scheme in ('http', 'https') else u.scheme
                path = u.path.rstrip('/')
                path = _re.sub(r'(v\d+)$', '', path)
                s = urlunparse((scheme, u.netloc.lower(), path, '', '', ''))
        except Exception:
            pass
        key = s.lower()
        if key in self._aliases:
            return self._aliases[key]
        return s

    def add_aliases(self, canonical: str, aliases: List[str]):
        can = str(self._canonicalize_id(canonical))
        for a in aliases:
            aa = str(self._canonicalize_id(a))
            self._aliases[aa.lower()] = can

    def close(self):
        if not self._use_memory and self._driver:
            self._driver.close()

    def run(self, cypher: str, **params):
        if self._use_memory or not getattr(self, "_driver", None):
            return []
        with self._driver.session() as session:  # type: ignore[attr-defined]
            return list(session.run(cypher, **params))  # type: ignore[arg-type]

    def ensure_indexes(self):
        if self._use_memory:
            return
        cypher = (
            "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;\n"
            "CREATE INDEX IF NOT EXISTS FOR (f:Fact) ON (f.id);"
        )
        self.run(cypher)

    def facts_by_subject(self, subject: str, limit: int = 20) -> List[Dict[str, Any]]:
        subj = self._canonicalize_id(subject)
        if self._use_memory:
            out = [dict(f) for f in self._mem_facts if f.get("subject") == subj]
            return out[:limit]
        cypher = "MATCH (f:Fact) WHERE f.subject = $subject RETURN f LIMIT $limit"
        rows = self.run(cypher, subject=subj, limit=limit)
        return [dict(row["f"]) for row in rows]

    def upsert_fact(self, fact: Dict[str, Any]):
        f = dict(fact)
        f["subject"] = self._canonicalize_id(f.get("subject"))
        f["object"] = self._canonicalize_id(f.get("object"))
        if self._use_memory:
            self._mem_facts = [x for x in self._mem_facts if x.get("id") != f.get("id")]
            self._mem_facts.append(f)
            return None
        cypher = (
            "MERGE (s:Entity {id: $subject})\n"
            "MERGE (o:Entity {id: $object})\n"
            "MERGE (s)-[r:REL {predicate: $predicate}]->(o)\n"
            "ON CREATE SET r.source_url=$source_url, r.truth_weight=$truth_weight, r.id=$id\n"
            "ON MATCH SET r.source_url=$source_url, r.truth_weight=$truth_weight\n"
            "MERGE (f:Fact {id: $id})\n"
            "SET f.subject=$subject, f.predicate=$predicate, f.object=$object, f.source_url=$source_url, f.truth_weight=$truth_weight\n"
        )
        self.run(cypher, **f)
        return None

    def search_facts(self, terms: List[str], limit: int = 8) -> List[Dict[str, Any]]:
        def score_fact(f: Dict[str, Any]) -> Dict[str, Any]:
            s = (str(f.get("subject", "")) + " " + str(f.get("predicate", "")) + " " + str(f.get("object", ""))).lower()
            hits = sum(1 for t in terms if t in s)
            if hits == 0:
                return {"score": 0.0, "corroboration_count": 0, "recency_weight": 0.0, "trust_score": float(f.get("truth_weight", 0.5) or 0.5), "trust_explain": "no term hits", "domain_score": 0.5}
            
            tw = float(f.get("truth_weight", 0.5) or 0.5)
            
            # Domain reputation scoring
            source_url = str(f.get("source_url", "") or "")
            domain_score = 0.5  # Default
            recency_weight_multiplier = 0.15  # Default
            
            try:
                from ..rag.domain_reputation import score_domain, get_recency_weight
                domain_score = score_domain(source_url)
                recency_weight_multiplier = get_recency_weight(source_url)
            except Exception:
                pass
            
            # Recency scoring with domain-specific decay
            ts = str(f.get("ts", "") or "")
            recency = 0.0
            if ts:
                try:
                    import datetime as _dt, math
                    year = int(ts[:4]) if len(ts) >= 4 and ts[:4].isdigit() else None
                    now_y = _dt.datetime.utcnow().year
                    age_years = max(0, (now_y - year)) if year else 3
                    recency = recency_weight_multiplier * math.exp(-float(age_years) / 4.0)
                except Exception:
                    recency = 0.08
            
            # Corroboration scoring
            corroboration = 0.0
            corroboration_count = 1
            if self._use_memory:
                sp = (f.get("subject"), f.get("predicate"))
                unique_sources = {g.get("source_url") for g in self._mem_facts if (g.get("subject"), g.get("predicate")) == sp}
                corroboration_count = max(1, len(unique_sources))
                corroboration = max(0.0, min(0.25, 0.06 * max(0, corroboration_count - 1)))
            
            # Trust score: combines truth_weight, domain reputation, and corroboration
            trust_score = 0.25 * tw + 0.25 * domain_score + 0.15 * corroboration
            
            # Total score: term hits + trust + recency
            # BOOST recency for recent facts (within 1 year)
            recency_boost = 1.0
            try:
                if ts:
                    import datetime as _dt
                    year = int(ts[:4]) if len(ts) >= 4 and ts[:4].isdigit() else None
                    now_y = _dt.datetime.utcnow().year
                    age_years = max(0, (now_y - year)) if year else 3
                    # If published this year or last year, apply 3x boost to recency
                    if age_years <= 1:
                        recency_boost = 3.0
            except:
                pass
            
            total = hits * 0.5 + trust_score + (recency * recency_boost)
            
            explain = f"hits={hits}*0.5 + trust={trust_score:.2f} (tw={tw:.2f}, domain={domain_score:.2f}, corr={corroboration_count}) + recency={recency:.2f}*{recency_boost:.1f}"
            
            return {
                "score": total,
                "corroboration_count": corroboration_count,
                "recency_weight": recency,
                "trust_score": trust_score,
                "trust_explain": explain,
                "domain_score": domain_score,
            }

        if self._use_memory:
            cand = []
            for f in self._mem_facts:
                detail = score_fact(f)
                if detail["score"] > 0:
                    g = dict(f)
                    g.update(detail)
                    cand.append(g)
            cand.sort(key=lambda x: x.get("score", 0.0), reverse=True)
            return cand[:limit]
        cypher = (
            "MATCH (f:Fact)\n"
            "WHERE any(t IN $terms WHERE f.subject CONTAINS t OR f.predicate CONTAINS t OR f.object CONTAINS t)\n"
            "RETURN f, (0.6*reduce(i IN $terms | CASE WHEN (f.subject CONTAINS i OR f.predicate CONTAINS i OR f.object CONTAINS i) THEN 1 ELSE 0 END, 0, (a,b) -> a+b) + 0.3*coalesce(f.truth_weight,0.5) + CASE WHEN coalesce(f.ts,'') <> '' THEN 0.1 ELSE 0 END) AS score\n"
            "ORDER BY score DESC\n"
            "LIMIT $limit"
        )
        rows = self.run(cypher, terms=terms, limit=limit)
        out: List[Dict[str, Any]] = []
        for row in rows:
            d = dict(row["f"])  # type: ignore
            d["score"] = row.get("score", 0.0)
            d["trust_score"] = 0.3 * float(d.get("truth_weight", 0.5) or 0.5)
            d["recency_weight"] = 0.1 if (d.get("ts") or "") else 0.0
            d["corroboration_count"] = None
            d["trust_explain"] = None
            out.append(d)
        return out
