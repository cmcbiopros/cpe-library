#!/usr/bin/env python3

import argparse
import importlib
import json
import os
import pkgutil
import re
import sys
from datetime import datetime, timedelta

from slugify import slugify

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)


def parse_args():
    parser = argparse.ArgumentParser(description="Run all capacity news scrapers.")
    parser.add_argument("--months", type=int, default=12, help="Backfill window in months.")
    parser.add_argument("--retention-years", type=int, default=5, help="Retention window in years.")
    parser.add_argument("--max-pages", type=int, default=20, help="Max pages to scan per provider.")
    parser.add_argument("--max-articles", type=int, default=0, help="Max articles total (0 = no limit).")
    parser.add_argument("--reprocess-existing", action="store_true", help="Re-parse and re-score existing articles.")
    parser.add_argument(
        "--reprocess-outlet",
        action="append",
        default=[],
        help="Limit reprocessing to a specific outlet name (repeatable)."
    )
    return parser.parse_args()


def load_existing_articles(data_file):
    if not os.path.exists(data_file):
        return []
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else data.get("articles", [])
    except Exception as exc:
        print(f"Error loading existing data: {exc}")
        return []


def normalize_article(article):
    return {
        "id": article.get("id", ""),
        "published_at": article.get("published_at") or article.get("published_date") or article.get("date") or "",
        "outlet": article.get("outlet") or article.get("source") or "Unknown",
        "title": article.get("title", "Untitled"),
        "url": article.get("url", ""),
        "status": article.get("status", "NOT_PERTINENT"),
        "company_primary": article.get("company_primary", ""),
        "event_types": article.get("event_types", []),
        "key_facts_text": article.get("key_facts_text", ""),
        "flags": article.get("flags", []),
        "has_bioreactor_L": article.get("has_bioreactor_L", False),
        "has_footprint": article.get("has_footprint", False),
        "has_fillfinish_output": article.get("has_fillfinish_output", False),
        "has_capex": article.get("has_capex", False),
        "facts": article.get("facts", [])
    }


def get_date_value(date_string):
    if not date_string:
        return None
    try:
        return datetime.fromisoformat(date_string.replace("Z", "+00:00"))
    except ValueError:
        try:
            return datetime.strptime(date_string, "%Y-%m-%d")
        except ValueError:
            return None


def load_providers():
    providers = []
    providers_dir = os.path.join(os.path.dirname(__file__), "providers")
    if not os.path.isdir(providers_dir):
        return providers

    for module_info in pkgutil.iter_modules([providers_dir]):
        if module_info.name.startswith("_") or module_info.name == "utils":
            continue
        module_name = f"scrapers.news.providers.{module_info.name}"
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            print(f"Error importing {module_name}: {exc}")
            continue

        provider_name = getattr(module, "PROVIDER_NAME", None)
        discover_fn = getattr(module, "discover_articles", None)
        parse_fn = getattr(module, "parse_article", None)
        if provider_name and callable(discover_fn) and callable(parse_fn):
            providers.append({
                "name": provider_name,
                "discover": discover_fn,
                "parse": parse_fn
            })
    return providers


def merge_articles(existing, new_articles):
    by_id = {article["url"]: article for article in existing if article.get("url")}
    for article in new_articles:
        if article.get("url"):
            by_id[article["url"]] = article
    return list(by_id.values()) + [article for article in existing if not article.get("url")]


def filter_retention(articles, retention_years):
    cutoff_date = datetime.utcnow() - timedelta(days=retention_years * 365)
    retained = []
    removed = 0

    for article in articles:
        date_value = get_date_value(article.get("published_at"))
        if date_value and date_value < cutoff_date:
            removed += 1
            continue
        retained.append(article)

    return retained, removed


BIOLOGICS_TERMS = [
    "monoclonal", "mab", "biologics", "vaccine", "viral vector", "aav", "lentiviral",
    "cell therapy", "gene therapy", "plasmid", "mrna", "lnp", "fill-finish",
    "aseptic", "lyophilization", "bioreactor", "single-use", "cell culture",
    "radioligand", "rlt", "radiopharmaceutical"
]

SMALL_MOLECULE_TERMS = [
    "small molecule", "api synthesis", "oral solid dose", "osd", "tablet",
    "capsule", "chemical synthesis"
]

MANUFACTURING_TERMS = [
    "manufacturing", "facility", "plant", "site", "campus", "suite", "line",
    "fill-finish", "bioreactor", "aseptic", "cleanroom", "cell culture"
]

EVENT_TYPE_RULES = {
    "expansion": [
        "capacity expansion", "expanding capacity", "expand capacity", "expanded capacity",
        "increase capacity", "increased capacity", "doubling capacity", "add capacity",
        "capacity upgrade", "capacity upgrade"
    ],
    "new_facility": [
        "new facility", "new site", "greenfield", "groundbreaking", "grand opening",
        "opened a facility", "opened a site", "opened a plant", "opened a campus",
        "opens a facility", "opens a site", "opens a plant", "opens a campus",
        "facility opening", "site opening", "plant opening", "campus opening"
    ],
    "construction": [
        "facility construction", "plant construction", "site construction",
        "under construction", "construction begins", "construction started",
        "retrofit facility", "retrofit plant", "retrofit site", "commissioning",
        "commissioned facility", "buildout", "ground-up build", "greenfield build"
    ],
    "shutdown": [
        "facility shutdown", "plant shutdown", "site shutdown", "facility closure",
        "plant closure", "site closure", "closure of a plant", "closure of the plant",
        "closure of its plant", "closure of a facility", "closure of the facility",
        "closure of its facility", "close its facility", "close its plant", "close its site",
        "closing its facility", "closing its plant", "closing its site",
        "closing the facility", "closing the plant", "closing the site",
        "mothball", "halted production", "halted operations",
        "suspend production", "suspended production", "shut down", "shut-down"
    ],
    "outsourcing": [
        "cdmo", "cmo", "contract manufacturing", "capacity reservation", "reserved capacity",
        "dedicated line", "dedicated suite", "long-term agreement", "manufacturing agreement",
        "outsourcing", "contracted manufacturing"
    ]
}

BIOREACTOR_PATTERN = re.compile(r"(\d{1,3}(?:,\d{3})*|\d+(?:\.\d+)?)\s*(?:x\s*)?(\d{1,3}(?:,\d{3})*|\d+(?:\.\d+)?)?\s*-?\s*(?:l|liter|liters|litre|litres)\b", re.IGNORECASE)
CAPACITY_L_PATTERN = re.compile(r"(\d{1,3}(?:,\d{3})*|\d+(?:\.\d+)?)(?:\s*(?:x\s*)?(\d{1,3}(?:,\d{3})*|\d+(?:\.\d+)?))?\s*-?\s*(?:l|liter|liters|litre|litres)\b", re.IGNORECASE)
FOOTPRINT_PATTERN = re.compile(r"(\d{1,3}(?:,\d{3})*|\d+(?:\.\d+)?|(?:one|two|three|four|five|six|seven|eight|nine|ten)(?:\s+and\s+a\s+half)?)\s*-?\s*(sq\.?\s*ft|sq ft|square\s*-?\s*feet|square\s*-?\s*foot|sqft|sqm|m2|m²)\b", re.IGNORECASE)
FILLFINISH_PATTERN = re.compile(r"(\d{1,3}(?:,\d{3})*|\d+(?:\.\d+)?|(?:one|two|three|four|five|six|seven|eight|nine|ten))\s*(million|billion)?\s*(vials|syringes|doses)\b", re.IGNORECASE)
FILLRATE_PATTERN = re.compile(r"(\d{1,3}(?:,\d{3})*|\d+(?:\.\d+)?|(?:one|two|three|four|five|six|seven|eight|nine|ten))\s*(vials|syringes|doses)\s*(?:per|/)\s*(minute|min|hour|hr)\b", re.IGNORECASE)
CAPEX_PATTERN = re.compile(r"(?:\$\s*)?(\d+(?:\.\d+)?)\s*(billion|million|b|m)\b", re.IGNORECASE)
CAPEX_NUMBER_PATTERN = re.compile(r"\$\s*(\d{1,3}(?:,\d{3})+(?:\.\d+)?)")


def split_sentences(text):
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def contains_any(text, terms):
    lowered = text.lower()
    return any(term in lowered for term in terms)


def normalize_capex(value, scale):
    try:
        amount = float(value)
    except ValueError:
        return None
    scale = scale.lower()
    if scale in ["billion", "b"]:
        return int(amount * 1_000_000_000)
    if scale in ["million", "m"]:
        return int(amount * 1_000_000)
    return None


def parse_numeric_value(raw_value):
    if raw_value is None:
        return None
    cleaned = str(raw_value).replace(",", "").strip().lower()
    word_numbers = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10
    }
    if cleaned in word_numbers:
        return word_numbers[cleaned]
    try:
        if "." in cleaned:
            return float(cleaned)
        return int(cleaned)
    except ValueError:
        return None


def extract_numeric_facts(text):
    facts = []
    has_bioreactor = False
    has_footprint = False
    has_fillfinish = False
    has_capex = False
    sales_terms = ["sales", "revenue", "earnings", "net income", "profit", "profitability", "ebitda", "quarter", "q1", "q2", "q3", "q4"]
    currency_terms = ["$", "usd", "us$", "dollar", "dollars", "eur", "€", "euro", "euros", "gbp", "£", "pound", "pounds"]
    capex_positive_terms = [
        "invest", "investment", "investing", "capex", "capital expenditure", "spend", "spending",
        "build", "construction", "facility", "plant", "site", "campus", "expansion", "expanded",
        "greenfield", "retrofit", "commissioning", "manufacturing", "production", "upgrade"
    ]
    capex_negative_terms = [
        "ad spend", "advertising", "marketing", "sales", "revenue", "earnings",
        "net income", "profit", "profitability", "ebitda", "price", "pricing",
        "lawsuit", "litigation", "settlement", "fine", "penalty", "damages",
        "insider trading", "allegations", "shares", "stock"
    ]

    for sentence in split_sentences(text):
        sentence_lower = sentence.lower()
        is_sales_context = contains_any(sentence_lower, sales_terms)
        is_capex_context = contains_any(sentence_lower, capex_positive_terms)
        is_non_capex_context = contains_any(sentence_lower, capex_negative_terms)
        has_currency = contains_any(sentence_lower, currency_terms)

        for match in BIOREACTOR_PATTERN.finditer(sentence):
            if not contains_any(sentence_lower, ["bioreactor", "single-use", "fermenter", "cell culture", "train"]):
                continue
            raw = match.group(0)
            primary_value = parse_numeric_value(match.group(1))
            secondary_value = parse_numeric_value(match.group(2)) if match.group(2) else None
            value_norm = None
            if primary_value is not None and secondary_value is not None:
                value_norm = primary_value * secondary_value
            else:
                value_norm = primary_value
            facts.append({
                "fact_type": "bioreactor_volume",
                "value_raw": raw,
                "value_norm": value_norm if value_norm is not None else "",
                "unit": "L",
                "evidence_snippet": sentence,
                "context": "bioreactor"
            })
            has_bioreactor = True

        for match in CAPACITY_L_PATTERN.finditer(sentence):
            if not contains_any(sentence_lower, ["capacity", "batch-fed", "cell culture", "manufacturing", "site", "facility", "plant"]):
                continue
            raw = match.group(0)
            primary_value = parse_numeric_value(match.group(1))
            secondary_value = parse_numeric_value(match.group(2)) if match.group(2) else None
            value_norm = None
            if primary_value is not None and secondary_value is not None:
                value_norm = primary_value * secondary_value
            else:
                value_norm = primary_value
            facts.append({
                "fact_type": "capacity_volume",
                "value_raw": raw,
                "value_norm": value_norm if value_norm is not None else "",
                "unit": "L",
                "evidence_snippet": sentence,
                "context": "capacity"
            })
            has_bioreactor = True

        for match in FOOTPRINT_PATTERN.finditer(sentence):
            if not contains_any(sentence_lower, ["facility", "site", "plant", "campus", "building", "cleanroom"]):
                continue
            raw = match.group(0)
            unit = match.group(2)
            value_norm = parse_numeric_value(match.group(1))
            if isinstance(value_norm, (int, float)) and "million" in raw.lower():
                value_norm = value_norm * 1_000_000
            facts.append({
                "fact_type": "facility_footprint",
                "value_raw": raw,
                "value_norm": value_norm if value_norm is not None else "",
                "unit": unit,
                "evidence_snippet": sentence,
                "context": "footprint"
            })
            has_footprint = True

        for match in FILLFINISH_PATTERN.finditer(sentence):
            if not contains_any(sentence_lower, ["per year", "annually", "/year", "per month", "annual"]):
                continue
            raw = match.group(0)
            value_norm = parse_numeric_value(match.group(1))
            magnitude = match.group(2)
            if isinstance(value_norm, (int, float)) and magnitude:
                if magnitude.lower() == "million":
                    value_norm = value_norm * 1_000_000
                elif magnitude.lower() == "billion":
                    value_norm = value_norm * 1_000_000_000
            facts.append({
                "fact_type": "fill_finish_output",
                "value_raw": raw,
                "value_norm": value_norm if value_norm is not None else "",
                "unit": match.group(3),
                "evidence_snippet": sentence,
                "context": "fill_finish"
            })
            has_fillfinish = True

        for match in FILLRATE_PATTERN.finditer(sentence):
            raw = match.group(0)
            value_norm = parse_numeric_value(match.group(1))
            if value_norm is None:
                continue
            unit = match.group(2)
            rate_unit = match.group(3)
            facts.append({
                "fact_type": "fill_finish_rate",
                "value_raw": raw,
                "value_norm": value_norm,
                "unit": f"{unit}/{rate_unit}",
                "evidence_snippet": sentence,
                "context": "fill_finish"
            })
            has_fillfinish = True

        capex_match = CAPEX_PATTERN.search(sentence)
        if capex_match:
            if is_sales_context or is_non_capex_context or not is_capex_context:
                continue
            if not has_currency:
                # Avoid "million liters" or other non-monetary quantities.
                continue
            raw = capex_match.group(0)
            value_norm = normalize_capex(capex_match.group(1), capex_match.group(2))
            facts.append({
                "fact_type": "capex",
                "value_raw": raw,
                "value_norm": value_norm if value_norm is not None else "",
                "unit": "USD",
                "evidence_snippet": sentence,
                "context": "investment"
            })
            has_capex = True
        else:
            if is_capex_context:
                if is_sales_context or is_non_capex_context:
                    continue
                capex_number = CAPEX_NUMBER_PATTERN.search(sentence)
                if capex_number:
                    raw = capex_number.group(0)
                    value_norm = parse_numeric_value(capex_number.group(1))
                    facts.append({
                        "fact_type": "capex",
                        "value_raw": raw,
                        "value_norm": value_norm if value_norm is not None else "",
                        "unit": "USD",
                        "evidence_snippet": sentence,
                        "context": "investment"
                    })
                    has_capex = True

    deduped = []
    seen = set()
    for fact in facts:
        if fact["fact_type"] == "capacity_volume":
            signature = (fact.get("value_norm"), fact.get("evidence_snippet"))
            if ("bioreactor_volume", signature) in seen:
                continue
        signature = (fact.get("value_norm"), fact.get("evidence_snippet"))
        seen.add((fact["fact_type"], signature))
        deduped.append(fact)

    return deduped, has_bioreactor, has_footprint, has_fillfinish, has_capex


def detect_event_types(text):
    event_types = []
    text_lower = text.lower()
    for event_type, phrases in EVENT_TYPE_RULES.items():
        if any(phrase in text_lower for phrase in phrases):
            event_types.append(event_type)
    # Catch closure language tied to facilities in the same sentence
    for sentence in split_sentences(text_lower):
        if any(term in sentence for term in ["closure", "closed", "closing", "shutter", "shut down"]):
            if any(term in sentence for term in ["plant", "facility", "site", "campus"]):
                if "shutdown" not in event_types:
                    event_types.append("shutdown")
                break
    return event_types


def build_article_id(outlet, published_at, title):
    slug = slugify(f"{outlet}-{published_at}-{title}")
    return slug[:120] if slug else slugify(f"{outlet}-{title}")


def analyze_article(title, body):
    combined_text = f"{title} {body}".strip()
    fact_source_text = body.strip() if body else combined_text
    facts, has_bioreactor, has_footprint, has_fillfinish, has_capex = extract_numeric_facts(fact_source_text)
    event_source_text = body.strip() if body else combined_text
    event_types = detect_event_types(event_source_text)
    has_biologics = contains_any(combined_text, BIOLOGICS_TERMS)
    has_small_molecule = contains_any(combined_text, SMALL_MOLECULE_TERMS)
    manufacturing_hit = contains_any(event_source_text, MANUFACTURING_TERMS)
    numeric_trigger = any([has_bioreactor, has_footprint, has_fillfinish, has_capex])

    status = "NOT_PERTINENT"
    flags = []
    has_signal = has_biologics or manufacturing_hit

    if has_small_molecule and not has_biologics:
        flags.append("SMALL_MOLECULE_ONLY")
    else:
        if has_biologics and (numeric_trigger or event_types or manufacturing_hit):
            status = "PERTINENT"
        elif numeric_trigger and not has_biologics:
            status = "NEEDS_REVIEW"
            flags.append("WEAK_BIOLOGICS_SIGNAL")

    if has_small_molecule and has_biologics:
        flags.append("SMALL_MOLECULE_MENTION")
        if status == "PERTINENT":
            status = "NEEDS_REVIEW"

    if status == "PERTINENT" and not facts:
        status = "NEEDS_REVIEW"
        flags.append("NO_NUMERIC_FACTS")

    if status == "NEEDS_REVIEW" and not facts and not event_types and has_signal:
        flags.append("BIO_MANUFACTURING_SIGNAL")

    if not facts and not event_types and not has_signal:
        status = "NOT_PERTINENT"

    if not body or len(body) < 400:
        if not facts:
            flags.append("LOW_EVIDENCE")
            if status == "PERTINENT":
                status = "NEEDS_REVIEW"

    return {
        "status": status,
        "flags": flags,
        "event_types": event_types,
        "facts": facts,
        "has_bioreactor_L": has_bioreactor,
        "has_footprint": has_footprint,
        "has_fillfinish_output": has_fillfinish,
        "has_capex": has_capex
    }


def key_facts_text_from_facts(facts):
    if not facts:
        return ""
    summaries = []
    for fact in facts:
        value = fact.get("value_raw") or ""
        summaries.append(f"{fact.get('fact_type', 'fact')}: {value}".strip())
    return "; ".join(summaries)


def reprocess_existing_articles(existing_articles, providers, max_articles, reprocess_outlets):
    provider_by_name = {provider["name"]: provider for provider in providers}
    provider_by_domain = {
        "bioprocessintl.com": provider_by_name.get("BioProcess International"),
        "pharmaceuticalcommerce.com": provider_by_name.get("Pharmaceutical Commerce"),
        "fiercepharma.com": provider_by_name.get("Fierce Pharma")
    }
    outlet_filter = {outlet.lower() for outlet in reprocess_outlets} if reprocess_outlets else None
    updated = []
    processed_count = 0

    for article in existing_articles:
        if max_articles and processed_count >= max_articles:
            updated.append(article)
            continue

        url = article.get("url")
        outlet = article.get("outlet")
        provider = provider_by_name.get(outlet)
        if not provider and url:
            for domain, fallback in provider_by_domain.items():
                if domain in url and fallback:
                    provider = fallback
                    break

        if not provider or not url:
            updated.append(article)
            continue
        if outlet_filter and provider["name"].lower() not in outlet_filter:
            updated.append(article)
            continue

        try:
            parsed = provider["parse"](url)
        except Exception:
            updated.append(article)
            continue

        parsed_title = parsed.get("title") or article.get("title") or "Untitled"
        parsed_body = parsed.get("body") or ""
        published_at = parsed.get("published_at") or article.get("published_at") or ""

        analysis = analyze_article(parsed_title, parsed_body)
        updated_article = {
            **article,
            "id": build_article_id(outlet or provider["name"], published_at, parsed_title),
            "title": parsed_title,
            "published_at": published_at,
            "status": analysis["status"],
            "event_types": analysis["event_types"],
            "key_facts_text": key_facts_text_from_facts(analysis["facts"]),
            "flags": analysis["flags"],
            "has_bioreactor_L": analysis["has_bioreactor_L"],
            "has_footprint": analysis["has_footprint"],
            "has_fillfinish_output": analysis["has_fillfinish_output"],
            "has_capex": analysis["has_capex"],
            "facts": analysis["facts"]
        }
        updated.append(updated_article)
        processed_count += 1

    return updated


def run_all_scrapers(months, retention_years, max_pages, max_articles, reprocess_existing, reprocess_outlets):
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    data_file = os.path.join(repo_root, "capacity-news", "capacity_news.json")
    os.makedirs(os.path.dirname(data_file), exist_ok=True)

    existing_articles = [normalize_article(article) for article in load_existing_articles(data_file)]
    providers = load_providers()
    if reprocess_existing:
        if reprocess_outlets:
            print(f"\nReprocessing existing articles for outlets: {', '.join(reprocess_outlets)}")
        else:
            print("\nReprocessing existing articles...")
        existing_articles = reprocess_existing_articles(existing_articles, providers, max_articles, reprocess_outlets)
    seen_urls = {article["url"] for article in existing_articles if article.get("url")}

    backfill_cutoff = datetime.utcnow() - timedelta(days=months * 30)
    new_articles = []

    for provider in providers:
        provider_name = provider["name"]
        print(f"\nRunning {provider_name}...")

        stats = {
            "discovered": 0,
            "new": 0,
            "skipped_seen": 0,
            "parsed_ok": 0,
            "parse_failed": 0,
            "pertinent": 0,
            "needs_review": 0
        }

        try:
            discovered = provider["discover"](backfill_cutoff, seen_urls, max_pages=max_pages)
        except Exception as exc:
            print(f"Error discovering articles for {provider_name}: {exc}")
            continue

        stats["discovered"] = len(discovered)
        if discovered:
            earliest = min(
                (item["published_at"] for item in discovered if item.get("published_at")),
                default=None
            )
            if earliest and earliest > backfill_cutoff:
                print(f"  RSS/listing does not reach full backfill window (earliest {earliest.date()})")

        for item in discovered:
            if max_articles and len(new_articles) >= max_articles:
                break

            url = item.get("url")
            if not url:
                continue
            if url in seen_urls:
                stats["skipped_seen"] += 1
                continue

            try:
                parsed = provider["parse"](url)
            except Exception as exc:
                print(f"  Parse failed for {url}: {exc}")
                stats["parse_failed"] += 1
                continue

            if not parsed:
                stats["parse_failed"] += 1
                continue

            parsed_title = parsed.get("title") or item.get("title") or "Untitled"
            parsed_body = parsed.get("body") or ""
            published_at = parsed.get("published_at") or ""
            if not published_at and item.get("published_at"):
                published_at = item["published_at"].strftime("%Y-%m-%d")

            analysis = analyze_article(parsed_title, parsed_body)
            if analysis["status"] == "PERTINENT":
                stats["pertinent"] += 1
            if analysis["status"] == "NEEDS_REVIEW":
                stats["needs_review"] += 1

            article = {
                "id": build_article_id(provider_name, published_at, parsed_title),
                "published_at": published_at,
                "outlet": provider_name,
                "title": parsed_title,
                "url": url,
                "status": analysis["status"],
                "company_primary": "",
                "event_types": analysis["event_types"],
                "key_facts_text": key_facts_text_from_facts(analysis["facts"]),
                "flags": analysis["flags"],
                "has_bioreactor_L": analysis["has_bioreactor_L"],
                "has_footprint": analysis["has_footprint"],
                "has_fillfinish_output": analysis["has_fillfinish_output"],
                "has_capex": analysis["has_capex"],
                "facts": analysis["facts"]
            }

            if not article["key_facts_text"] and "BIO_MANUFACTURING_SIGNAL" in article["flags"]:
                article["key_facts_text"] = "Biologics/manufacturing signal"

            new_articles.append(article)
            seen_urls.add(url)
            stats["new"] += 1
            stats["parsed_ok"] += 1

        print(
            f"  discovered={stats['discovered']} new={stats['new']} skipped_seen={stats['skipped_seen']} "
            f"parsed_ok={stats['parsed_ok']} parse_failed={stats['parse_failed']} "
            f"pertinent={stats['pertinent']} needs_review={stats['needs_review']}"
        )

    combined_articles = merge_articles(existing_articles, new_articles)
    combined_articles, removed_count = filter_retention(combined_articles, retention_years)
    combined_articles.sort(key=lambda item: get_date_value(item.get("published_at")) or datetime.min, reverse=True)

    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(combined_articles, f, indent=2, ensure_ascii=False)

    print(f"\nFinal result: {len(combined_articles)} total articles")
    print(f"Added {len(new_articles)} new articles")
    print(f"Removed {removed_count} articles older than {retention_years} years")
    print(f"Output written to {data_file}")


if __name__ == "__main__":
    args = parse_args()
    run_all_scrapers(
        args.months,
        args.retention_years,
        args.max_pages,
        args.max_articles,
        args.reprocess_existing,
        args.reprocess_outlet
    )
