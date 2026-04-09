"""
fetch_ptab_data.py
------------------
Part 3 pre-processor for the InterDigital v Amazon swarm analysis.

Fetches live PTAB IPR and reexamination data from the USPTO Open Data
Portal API, combines with the Part 2 enriched input, and writes a
Part 3 enriched input file that the existing swarm consumes unchanged.

Run this BEFORE main.py:
    python fetch_ptab_data.py
    python -m app.main

Requirements:
    pip install requests python-dotenv
"""

import os
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load environment
# ---------------------------------------------------------------------------

load_dotenv()

USPTO_ODP_API_KEY = os.getenv("USPTO_ODP_API_KEY")
if not USPTO_ODP_API_KEY:
    raise ValueError("USPTO_ODP_API_KEY not found in .env file")

ODP_BASE_URL = "https://api.uspto.gov/api/v1"

ODP_HEADERS = {
    "X-API-KEY": USPTO_ODP_API_KEY,
    "Content-Type": "application/json",
}

# ---------------------------------------------------------------------------
# PTAB proceedings of interest
# The API uses POST with a structured filters body:
# {
#   "filters": [{"name": "field.path", "value": ["value"]}],
#   "pagination": {"offset": 0, "limit": 10}
# }
# Field paths confirmed from USPTO ODP API mapping documentation.
# ---------------------------------------------------------------------------

PTAB_SEARCHES = [
    {
        "label": "Dolby IPR against InterDigital US 9,185,268",
        "description": "Dolby filed IPR petition against InterDigital patent "
                       "US 9,185,268 (chromatic correction/display technology) "
                       "in February 2026. Patent was being asserted by "
                       "InterDigital against The Walt Disney Company. Signals "
                       "fracture in the licensor coalition — both Dolby and "
                       "InterDigital are in Access Advance HEVC pool.",
        "filters": [
            {"name": "patentOwnerData.patentOwnerName", "value": ["InterDigital"]},
            {"name": "regularPetitionerData.petitionerName", "value": ["Dolby"]},
        ],
    },
    {
        "label": "All IPRs against InterDigital",
        "description": "Broader search for IPR petitions challenging "
                       "InterDigital patents in any technology space.",
        "filters": [
            {"name": "patentOwnerData.patentOwnerName", "value": ["InterDigital"]},
            {"name": "trialMetaData.trialTypeCode", "value": ["IPR"]},
        ],
    },
    {
        "label": "InterDigital US 10,805,610 all proceedings",
        "description": "Unified Patents filed ex parte reexamination of "
                       "InterDigital US Patent 10,805,610 (coding groups of "
                       "pixels within blocks). CRU granted August 7, 2025.",
        "filters": [
            {"name": "patentOwnerData.patentNumber", "value": ["10805610"]},
        ],
    },
    {
        "label": "Amazon IPR petitions",
        "description": "Search for IPRs filed by Amazon against any patent "
                       "holder — indicates Amazon's PTAB strategy.",
        "filters": [
            {"name": "regularPetitionerData.petitionerName", "value": ["Amazon"]},
            {"name": "trialMetaData.trialTypeCode", "value": ["IPR"]},
        ],
    },
]

# ---------------------------------------------------------------------------
# Key patents in the InterDigital v Amazon dispute for direct lookup
# ---------------------------------------------------------------------------

KEY_PATENTS = [
    {
        "number": "10741211",
        "label": "US 10,741,211 — ITC/Delaware assertion",
        "notes": "One of five video codec patents asserted in ITC 337-TA-3869 "
                 "and District of Delaware companion case 1:25-cv-01365."
    },
    {
        "number": "9747674",
        "label": "US 9,747,674 — ITC/Delaware assertion",
        "notes": "One of five video codec patents asserted in ITC 337-TA-3869 "
                 "and District of Delaware companion case."
    },
    {
        "number": "8149338",
        "label": "US 8,149,338 — Eastern District of Virginia assertion",
        "notes": "One of four video coding patents asserted in Eastern District "
                 "of Virginia case 2:25-cv-00822."
    },
    {
        "number": "9185268",
        "label": "US 9,185,268 — Subject of Dolby IPR petition",
        "notes": "Chromatic correction/display technology. Asserted by "
                 "InterDigital against Disney. Dolby filed IPR petition "
                 "against this patent in February 2026."
    },
    {
        "number": "10805610",
        "label": "US 10,805,610 — Subject of Unified Patents reexamination",
        "notes": "Coding groups of pixels within blocks. Asserted against "
                 "Disney. Unified Patents ex parte reexamination granted "
                 "August 7, 2025."
    },
]


# ---------------------------------------------------------------------------
# USPTO ODP API functions
# ---------------------------------------------------------------------------

def search_ptab_proceedings(filters: list, label: str, max_results: int = 10) -> list:
    """
    Search PTAB proceedings via USPTO ODP API.

    Uses POST with structured JSON body per the ODP API mapping spec:
    POST /api/v1/patent/trials/proceedings/search
    Body: {
        "filters": [{"name": "field.path", "value": ["value"]}],
        "pagination": {"offset": 0, "limit": N}
    }
    """
    url = f"{ODP_BASE_URL}/patent/trials/proceedings/search"

    payload = {
        "filters": filters,
        "pagination": {
            "offset": 0,
            "limit": max_results,
        },
    }

    print(f"  Searching: {label}")
    print(f"  Payload: {json.dumps(payload)}")
    time.sleep(2)  # Avoid rate limiting

    try:
        response = requests.post(
            url,
            headers=ODP_HEADERS,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            results = data.get("trialMetaDataBag", [])
            count = data.get("count", len(results))
            print(f"  Found {count} total, returned {len(results)} proceedings")
            return results
        else:
            print(f"  Warning: HTTP {response.status_code}")
            print(f"  Response: {response.text[:400]}")
            return []

    except requests.RequestException as e:
        print(f"  Error: {e}")
        return []


def search_patent_ptab_history(patent_number: str, label: str) -> list:
    """Search all PTAB proceedings for a specific patent number."""
    url = f"{ODP_BASE_URL}/patent/trials/proceedings/search"

    payload = {
        "filters": [
            {"name": "patentOwnerData.patentNumber", "value": [patent_number]},
        ],
        "pagination": {
            "offset": 0,
            "limit": 20,
        },
    }

    print(f"  Patent history for {patent_number}: {label}")
    time.sleep(2)

    try:
        response = requests.post(
            url,
            headers=ODP_HEADERS,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            results = data.get("trialMetaDataBag", [])
            print(f"  Found {len(results)} proceedings")
            return results
        else:
            print(f"  Warning: HTTP {response.status_code} — {response.text[:300]}")
            return []

    except requests.RequestException as e:
        print(f"  Error: {e}")
        return []


# ---------------------------------------------------------------------------
# Build PTAB fact section
# ---------------------------------------------------------------------------

def format_proceeding(proc: dict) -> str:
    """Format a single PTAB proceeding."""
    trial_meta = proc.get("trialMetaData", {})
    patent_owner = proc.get("patentOwnerData", {})
    petitioner = proc.get("regularPetitionerData", {})

    lines = []
    lines.append(f"Trial: {trial_meta.get('trialNumber', proc.get('trialNumber', 'Unknown'))}")
    lines.append(f"Type: {trial_meta.get('trialTypeCode', 'Unknown')}")
    lines.append(f"Status: {trial_meta.get('trialStatusCategory', 'Unknown')}")
    lines.append(f"Patent: {patent_owner.get('patentNumber', 'Unknown')}")
    lines.append(f"Owner: {patent_owner.get('patentOwnerName', 'Unknown')}")
    lines.append(f"Petitioner: {petitioner.get('petitionerName', 'Unknown')}")
    lines.append(f"Filed: {trial_meta.get('accordedFilingDate', 'Unknown')}")
    lines.append(f"Institution: {trial_meta.get('institutionDecisionDate', 'Pending')}")
    lines.append(f"Final Decision: {trial_meta.get('latestDecisionDate', 'Pending')}")
    return "\n    ".join(lines)


def build_ptab_section(search_results: dict, patent_history: dict) -> str:
    """Build the complete PTAB fact layer for the enriched input file."""
    lines = []
    lines.append("=" * 70)
    lines.append("PTAB VALIDITY CHALLENGE LAYER — ENRICHED FACT LAYER")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("Source: USPTO Open Data Portal PTAB API + verified research")
    lines.append("=" * 70)
    lines.append("")
    lines.append("PTAB ENVIRONMENT CONTEXT (2025-2026):")
    lines.append("")
    lines.append("Under USPTO Director John Squires (confirmed September 2025):")
    lines.append("- IPR institution rates dropped from 68% (2024) to below")
    lines.append("  40% as of December 2025")
    lines.append("- Discretionary denial rates rose to 60% under new")
    lines.append("  bifurcated process (effective October 20, 2025)")
    lines.append("- Director personally controls institution decisions")
    lines.append("- Half of all petitions in Oct 2025-Jan 2026 window were")
    lines.append("  discretionarily denied outright")
    lines.append("- This environment FAVORS InterDigital as patent owner")
    lines.append("")
    lines.append("KEY PTAB PROCEEDINGS (verified research):")
    lines.append("")
    lines.append("1. DOLBY IPR AGAINST INTERDIGITAL US 9,185,268")
    lines.append("-" * 50)
    lines.append("Filed: February 2026")
    lines.append("Petitioner: Dolby Laboratories")
    lines.append("Patent Owner: InterDigital")
    lines.append("Patent: US 9,185,268 (chromatic correction/display technology)")
    lines.append("Asserted against: The Walt Disney Company")
    lines.append("")
    lines.append("Strategic significance:")
    lines.append("- Dolby and InterDigital are both in Access Advance HEVC pool")
    lines.append("- Dolby filing against InterDigital = licensor coalition fracture")
    lines.append("- ~60% discretionary denial rate means institution uncertain")
    lines.append("- Final written decision if instituted: 2027-2028 at earliest")
    lines.append("- Indirect signal to Amazon: portfolio has validity exposure")
    lines.append("")
    lines.append("2. UNIFIED PATENTS REEXAMINATION — US 10,805,610")
    lines.append("-" * 50)
    lines.append("Filed: July 2025 | Granted: August 7, 2025")
    lines.append("Challenger: Unified Patents (implementer consortium)")
    lines.append("Patent Owner: InterDigital VC Holdings")
    lines.append("Patent: US 10,805,610 (pixel block coding)")
    lines.append("Asserted against: The Walt Disney Company")
    lines.append("")
    lines.append("Strategic significance:")
    lines.append("- CRU found substantial new questions of patentability")
    lines.append("- Ex parte reexamination continues independently of settlement")
    lines.append("- Amazon may be Unified Patents member/beneficiary")
    lines.append("- Claim cancellation removes this patent from the portfolio")
    lines.append("")
    lines.append("3. AMAZON PTAB STRATEGY")
    lines.append("-" * 50)
    lines.append("- Amazon filed IPRs against Nokia (IPR2024-00847/00848)")
    lines.append("  in May 2024 — demonstrates willingness to use PTAB")
    lines.append("- Amazon has NOT filed IPRs against InterDigital's current")
    lines.append("  asserted patents — deliberate strategic choice")
    lines.append("- Estoppel risk, timing, and Director Squires environment")
    lines.append("  all counsel against premature PTAB filing")
    lines.append("")

    # Live API results
    lines.append("4. LIVE USPTO ODP API RESULTS")
    lines.append("-" * 50)
    any_results = False
    for label, results in search_results.items():
        lines.append(f"\nQuery: {label}")
        if results:
            any_results = True
            for proc in results[:5]:
                lines.append(f"  ---")
                lines.append(f"  {format_proceeding(proc)}")
        else:
            lines.append("  No live API results for this query")

    lines.append("")
    lines.append("5. PATENT-LEVEL PTAB HISTORY (live API)")
    lines.append("-" * 50)
    for patent_label, history in patent_history.items():
        lines.append(f"\nPatent: {patent_label}")
        if history:
            any_results = True
            for proc in history[:3]:
                trial_meta = proc.get("trialMetaData", {})
                petitioner_data = proc.get("regularPetitionerData", {})
                lines.append(f"  Trial: {trial_meta.get('trialNumber', 'Unknown')}")
                lines.append(f"  Type: {trial_meta.get('trialTypeCode', 'Unknown')}")
                lines.append(f"  Status: {trial_meta.get('trialStatusCategory', 'Unknown')}")
                lines.append(f"  Petitioner: {petitioner_data.get('petitionerName', 'Unknown')}")
                lines.append(f"  Filed: {trial_meta.get('accordedFilingDate', 'Unknown')}")
                lines.append("")
        else:
            lines.append("  No live API results for this patent")

    if not any_results:
        lines.append("")
        lines.append("Note: USPTO ODP API returned no live results for these")
        lines.append("specific queries. Verified research data above is sourced")
        lines.append("from IP Fray (Feb 10, 2026), Unified Patents (Aug 8, 2025),")
        lines.append("and public PTAB and court records.")

    lines.append("")
    lines.append("STANDARDS ESSENTIALITY CONTEXT:")
    lines.append("")
    lines.append("TECHNICAL vs COMMERCIAL ESSENTIALITY:")
    lines.append("- Technically essential: no feasible way to implement the")
    lines.append("  standard without infringing — FRAND obligation attaches")
    lines.append("- Commercially essential: alternatives exist technically")
    lines.append("  but not practically — NO FRAND obligation under strict")
    lines.append("  reading of ETSI and similar IPR policies")
    lines.append("")
    lines.append("ENCODING vs DECODING DISTINCTION:")
    lines.append("- HEVC and related standards specify DECODER behavior only")
    lines.append("- Encoder implementations are deliberately left unspecified")
    lines.append("- Encoder-side patents may be commercially essential but")
    lines.append("  NOT technically essential — no FRAND commitment")
    lines.append("- Internal decode loop: encoders internally decode as a")
    lines.append("  quality check — whether this brings encoder-side patents")
    lines.append("  within FRAND scope is legally unresolved")
    lines.append("")
    lines.append("INTERDIGITAL'S ARGUMENT:")
    lines.append("- Encoding is not standardized — only decoding is specified")
    lines.append("- Encoder-side patents carry no FRAND commitment")
    lines.append("- This is NOT a FRAND rate-setting case for those patents")
    lines.append("")
    lines.append("AMAZON'S COUNTER-ARGUMENT:")
    lines.append("- Commercial reality makes encoder-side patents functionally")
    lines.append("  indistinguishable from technically essential ones")
    lines.append("- FRAND framework should apply to commercially essential")
    lines.append("  patents — UK court should set a RAND rate accordingly")
    lines.append("")
    lines.append("HDR PATENTS — ADDITIONAL COMPLEXITY:")
    lines.append("- HDR processing occurs on BOTH encode and decode sides")
    lines.append("- HDR patents are the most legally vulnerable subset —")
    lines.append("  dual-side nature makes clean essentiality argument hard")
    lines.append("")
    lines.append("REGULATORY / COMPETITION CONTEXT:")
    lines.append("")
    lines.append("EDGIO ACQUISITION PATTERN:")
    lines.append("- InterDigital acquired content delivery patents from")
    lines.append("  Edgio Inc. bankruptcy via DRNC Holdings, January 2025")
    lines.append("  — seven months before Amazon filed in UK August 2025")
    lines.append("- Non-SEP patents, no FRAND commitment")
    lines.append("- No organic InterDigital presence in content delivery")
    lines.append("- Deployed in Western District of Texas February 2026")
    lines.append("- Question: improper patent assembly against FRAND")
    lines.append("  negotiating counterparty under Article 102 TFEU?")
    lines.append("")
    lines.append("EC NOTIFICATION (24 December 2025):")
    lines.append("- UPC Mannheim notified European Commission of AILI orders")
    lines.append("- Commission is now an active potential competition authority")
    lines.append("- EC investigation would constrain InterDigital enforcement")
    lines.append("  posture across ALL licensees simultaneously")
    lines.append("- Amazon's abuse of dominance claim (UK High Court) not")
    lines.append("  yet disposed of — could result in damages TO Amazon")
    lines.append("")
    lines.append("=" * 70)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------

def main():
    print("\n" + "=" * 60)
    print("InterDigital v Amazon — Part 3 PTAB Data Fetcher")
    print("=" * 60)

    base_path = "inputs/part2_enriched_input.txt"
    if not os.path.exists(base_path):
        raise FileNotFoundError(
            f"Part 2 enriched input not found at {base_path}. "
            "Please run fetch_us_dockets.py first."
        )

    with open(base_path, "r", encoding="utf-8") as f:
        part2_content = f.read()

    print(f"\nLoaded Part 2 enriched input: {len(part2_content)} characters")

    print("\n--- Fetching live PTAB data from USPTO ODP API ---")
    search_results = {}
    patent_history = {}

    for search in PTAB_SEARCHES:
        print(f"\nProcessing: {search['label']}")
        results = search_ptab_proceedings(
            filters=search["filters"],
            label=search["label"],
        )
        search_results[search["label"]] = results

    print("\n--- Fetching PTAB history for key patents ---")
    for patent in KEY_PATENTS:
        history = search_patent_ptab_history(
            patent_number=patent["number"],
            label=patent["label"],
        )
        patent_history[patent["label"]] = history

    raw_data = {
        "search_results": search_results,
        "patent_history": patent_history,
    }

    os.makedirs("outputs", exist_ok=True)
    json_path = "outputs/ptab_raw_data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, indent=2, default=str)
    print(f"\nRaw PTAB data saved: {json_path}")

    print("\n--- Building PTAB enriched fact layer ---")
    ptab_section = build_ptab_section(search_results, patent_history)

    part3_content = f"""INTERDIGITAL v AMAZON — PART 3 ENRICHED ANALYSIS INPUT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This file builds on the Part 2 enriched input by adding:
1. PTAB validity challenge data (USPTO ODP API + verified research)
2. Standards essentiality context (technical vs commercial essentiality)
3. Regulatory/competition law context (Edgio acquisition, EC notification)

Three new agents analyse these dimensions:
- PTAB/Validity Agent
- Regulatory/Competition Agent
- Standards Essentiality Agent

{'=' * 70}
PART 2 ENRICHED CONTENT (US DOCKETS + ORIGINAL JUVE ARTICLE)
{'=' * 70}

{part2_content}

{ptab_section}
"""

    output_path = "inputs/part3_enriched_input.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(part3_content)

    print(f"\nPart 3 enriched input written: {output_path}")
    print(f"Total length: {len(part3_content):,} characters")

    print("\n--- Next steps ---")
    print("1. Run: python -m app.main")
    print("\nPart 3 analysis ready to run.")
    print("=" * 60)


if __name__ == "__main__":
    main()
