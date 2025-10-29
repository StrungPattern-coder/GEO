# GEO Protocol v1.0 Specification

**Generative Engine Optimization Protocol**  
**Version:** 1.0  
**Status:** Draft  
**Last Updated:** October 29, 2025

---

## Executive Summary

The GEO Protocol is a new standard for content optimization in the age of Generative AI. While traditional SEO focuses on ranking in search results, GEO focuses on becoming a **trusted source of truth** that AI engines can confidently cite.

### Key Principles
1. **Structured Over Unstructured**: Data is provided in machine-readable formats
2. **Verifiable Over Claimed**: Facts include evidence and confidence scores
3. **Canonical Over Duplicate**: Entities have unique IDs with aliases
4. **Transparent Over Opaque**: Publishers sign their data cryptographically

---

## Protocol Overview

### GEO Sitemap
Publishers create a `geo-sitemap.json` file at their domain root (similar to `robots.txt` or `sitemap.xml`):

```
https://example.com/geo-sitemap.json
```

This file contains:
- **Publisher identity** (name, domain, verification)
- **Entities** (canonical URIs, types, aliases, properties)
- **Facts** (subject-predicate-object triples with metadata)
- **Signature** (cryptographic proof of authenticity)

### Discovery
GEO engines discover sitemaps via:
1. Well-known URL: `/.well-known/geo-sitemap.json`
2. HTTP Link header: `Link: </geo-sitemap.json>; rel="geo-sitemap"`
3. Meta tag: `<link rel="geo-sitemap" href="/geo-sitemap.json">`
4. Publisher registration (opt-in registry)

---

## Schema Reference

### Publisher Object
```json
{
  "name": "string (required)",
  "domain": "hostname (required)",
  "verified": "boolean (optional, default: false)",
  "contact": "email (optional)"
}
```

**Verification Process:**
1. Publisher submits GEO sitemap URL
2. Engine fetches sitemap from `domain` over HTTPS
3. Engine sends verification email to `contact`
4. Publisher confirms via signed token
5. `verified` flag set to `true` in engine's database

---

### Entity Object
```json
{
  "id": "uri (required) - canonical identifier",
  "type": "enum (required) - Person|Organization|Paper|Product|Concept|Event|Location|Other",
  "name": "string (optional) - human-readable name",
  "aliases": ["uri[]"] - alternative identifiers,
  "properties": {
    /* type-specific key-value pairs */
  }
}
```

**Entity Types:**
- **Person**: Researchers, authors, creators
  - Properties: `affiliation`, `title`, `expertise[]`, `orcid`, `h-index`
- **Organization**: Companies, universities, labs
  - Properties: `industry`, `founded`, `location`, `size`
- **Paper**: Research papers, articles
  - Properties: `year`, `venue`, `doi`, `citations`, `keywords[]`
- **Product**: Software, hardware, services
  - Properties: `version`, `category`, `license`, `pricing`
- **Concept**: Ideas, theories, algorithms
  - Properties: `definition`, `relatedConcepts[]`, `applications[]`
- **Event**: Conferences, releases, milestones
  - Properties: `date`, `location`, `attendees`
- **Location**: Physical places
  - Properties: `coordinates`, `address`, `region`

---

### Fact Object
```json
{
  "subject": "uri (required) - entity ID",
  "predicate": "string (required) - relationship type",
  "object": "uri|string|number|boolean (required)",
  "confidence": "float 0.0-1.0 (required) - publisher certainty",
  "timestamp": "ISO 8601 datetime (optional)",
  "evidence": ["uri[]"] - supporting sources,
  "temporal": {
    "validFrom": "datetime",
    "validUntil": "datetime"
  }
}
```

**Common Predicates:**
- **Authorship**: `authored`, `coAuthored`, `edited`
- **Employment**: `worksAt`, `foundedBy`, `employed`
- **Relations**: `relatesTo`, `similarTo`, `partOf`, `hasProperty`
- **Citations**: `cites`, `citedBy`, `references`
- **Attributes**: `title`, `abstract`, `description`, `hasURL`

**Confidence Scoring:**
- `1.0` = Absolute certainty (direct assertion by authoritative source)
- `0.9` = Very high confidence (multiple corroborating sources)
- `0.7` = High confidence (single reliable source)
- `0.5` = Medium confidence (inferred or derived)
- `<0.5` = Low confidence (speculative or uncertain)

---

### Signature
Publishers MUST sign their GEO sitemaps to prevent tampering.

**Algorithm:** HMAC-SHA256 or Ed25519

**Signing Process:**
1. Canonicalize JSON (sort keys, remove whitespace)
2. Concatenate: `domain + "\n" + canonical_json`
3. Sign with private key
4. Base64-encode signature
5. Add to sitemap: `"signature": "sha256:<base64>"`

**Verification:**
1. Engine fetches sitemap over HTTPS
2. Extracts `publisher.domain` and `signature`
3. Reconstructs canonical payload
4. Verifies signature with publisher's public key (from registry)
5. Rejects if signature invalid

---

## Integration Guide

### For Publishers

#### Step 1: Create Entities
```json
{
  "entities": [
    {
      "id": "https://yourdomain.com/person/john-doe",
      "type": "Person",
      "name": "John Doe",
      "properties": {
        "title": "Chief Scientist",
        "affiliation": "YourCompany"
      }
    }
  ]
}
```

#### Step 2: Define Facts
```json
{
  "facts": [
    {
      "subject": "https://yourdomain.com/person/john-doe",
      "predicate": "worksAt",
      "object": "YourCompany",
      "confidence": 1.0,
      "timestamp": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### Step 3: Sign Sitemap
Use provided SDK:
```python
from geo_protocol import GEOSitemap, sign_sitemap

sitemap = GEOSitemap(publisher={...}, entities=[...], facts=[...])
signed = sign_sitemap(sitemap, private_key="your-key")
signed.save("geo-sitemap.json")
```

#### Step 4: Publish
Upload `geo-sitemap.json` to:
- `https://yourdomain.com/.well-known/geo-sitemap.json`
- OR `https://yourdomain.com/geo-sitemap.json`

#### Step 5: Register
Submit to GEO registry:
```bash
curl -X POST https://geo-registry.org/submit \
  -H "Content-Type: application/json" \
  -d '{"domain": "yourdomain.com", "sitemap_url": "https://yourdomain.com/geo-sitemap.json"}'
```

---

### For Engine Developers

#### Ingestion Workflow
1. **Discovery**: Crawl registered domains for GEO sitemaps
2. **Fetch**: Download sitemap over HTTPS
3. **Validate**: Check JSON schema compliance
4. **Verify**: Validate cryptographic signature
5. **Parse**: Extract entities and facts
6. **Canonicalize**: Normalize entity IDs and aliases
7. **Merge**: Integrate into knowledge graph
8. **Rank**: Assign trust scores based on publisher reputation and confidence

#### Trust Scoring
```python
trust_score = (
    publisher_reputation * 0.4 +
    fact_confidence * 0.3 +
    corroboration_factor * 0.2 +
    recency_weight * 0.1
)
```

---

## API Endpoint

GEO engines SHOULD expose an endpoint for dynamic submissions:

### POST /geo/submit
```json
{
  "publisher": {...},
  "entities": [...],
  "facts": [...],
  "signature": "..."
}
```

**Response:**
```json
{
  "status": "accepted|rejected",
  "facts_ingested": 42,
  "entities_created": 5,
  "errors": []
}
```

---

## Best Practices

### For Publishers
1. ✅ Use stable, persistent URIs for entities
2. ✅ Include evidence URLs for controversial facts
3. ✅ Update sitemaps regularly (weekly or on content change)
4. ✅ Set realistic confidence scores (don't claim 1.0 for uncertain facts)
5. ✅ Use aliases to link your entities to external identifiers (ORCID, DOI, etc.)
6. ❌ Don't fabricate facts to game rankings
7. ❌ Don't reuse entity IDs for different concepts

### For Engines
1. ✅ Respect publisher confidence scores
2. ✅ Weight publisher reputation heavily
3. ✅ Corroborate facts across multiple sources
4. ✅ Penalize publishers with low-quality or misleading data
5. ✅ Provide feedback to publishers on fact acceptance rates
6. ❌ Don't blindly trust all submissions
7. ❌ Don't favor paid or premium publishers over organic quality

---

## Roadmap

### v1.1 (Q1 2026)
- Multi-language support
- Pagination for large sitemaps
- Incremental updates (delta sitemaps)
- Rich media support (images, videos)

### v2.0 (Q3 2026)
- Reasoning chains (explain how facts were derived)
- Probabilistic facts (Bayesian confidence)
- Real-time streaming updates (WebSub)
- Federated trust networks

---

## Community

- **Website**: https://geo-protocol.org
- **GitHub**: https://github.com/geo-protocol
- **Registry**: https://geo-registry.org
- **Forum**: https://discuss.geo-protocol.org
- **Spec Issues**: https://github.com/geo-protocol/spec/issues

---

## License

This specification is released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Implementations may use any license.

---

**Join the revolution.** Make your content a source of truth for the AI age.
