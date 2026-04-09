"""
fetch_us_dockets.py
-------------------
Part 2 pre-processor for the InterDigital v Amazon swarm analysis.

Fetches live docket data from CourtListener for all four US proceedings,
combines with the original JUVE article, and writes an enriched input file
that the existing swarm (main.py) consumes unchanged.

Run this BEFORE main.py:
    python fetch_us_dockets.py
    python -m app.main

Requirements:
    pip install requests python-dotenv
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load environment
# ---------------------------------------------------------------------------

load_dotenv()

COURTLISTENER_API_KEY = os.getenv("COURTLISTENER_API_KEY")
if not COURTLISTENER_API_KEY:
    raise ValueError("COURTLISTENER_API_KEY not found in .env file")

HEADERS = {
    "Authorization": f"Token {COURTLISTENER_API_KEY}",
    "Content-Type": "application/json",
}

BASE_URL = "https://www.courtlistener.com/api/rest/v4"

# ---------------------------------------------------------------------------
# US Proceedings to fetch
# Four cases identified in research - all InterDigital v Amazon
# ---------------------------------------------------------------------------

US_CASES = [
    {
        "label": "District of Delaware (stayed ITC companion)",
        "docket_number": "1:25-cv-01365",
        "court": "ded",
        "courtlistener_id": "71892898",
        "status": "STAYED",
        "notes": "Companion to ITC 337-TA-3869. Stayed pending ITC resolution. "
                 "Five video codec patents asserted: US 10,741,211; 9,747,674; "
                 "8,363,724; 8,681,855; 11,917,146. Filed November 7, 2025.",
    },
    {
        "label": "Eastern District of Virginia (active)",
        "docket_number": "2:25-cv-00822",
        "court": "vaed",
        "courtlistener_id": "72061224",
        "status": "ACTIVE",
        "notes": "Originally filed as 1:25-cv-02390 (Alexandria Division), "
                 "transferred to Norfolk Division. Four different video coding "
                 "patents asserted: US 8,149,338; 11,252,435; 12,143,606; "
                 "12,149,734. Filed December 18, 2025. Assigned to District Judge "
                 "Arenda L. Wright Allen. Represented by McKool Smith PC.",
    },
    {
        "label": "ITC Investigation 337-TA-3869 (primary US enforcement lever)",
        "docket_number": "337-TA-3869",
        "court": "itc",
        "courtlistener_id": None,  # ITC not in CourtListener — handled separately
        "status": "ACTIVE",
        "notes": "Filed December 2025. Five video codec patents asserted — same "
                 "five as the Delaware companion case. Primary US enforcement "
                 "mechanism. Seeks exclusion order blocking import of Amazon "
                 "FireTV, Kindle, and Echo Show devices into the United States. "
                 "An exclusion order would create acute commercial disruption "
                 "independent of any European penalty. Delaware district case is "
                 "stayed as companion to this ITC investigation.",
    },
    {
        "label": "Western District of Texas, Midland/Odessa Division (content delivery patents)",
        "docket_number": "pending",
        "court": "txwd",
        "courtlistener_id": None,  # Filed February 2026, may not yet be in CourtListener
        "status": "ACTIVE",
        "notes": "Filed February 2026 by InterDigital and subsidiary DRNC Holdings "
                 "(patents acquired from Edgio Inc. in January 2025). Six content "
                 "delivery patents asserted: US 7,921,259; 10,116,565; 8,745,128; "
                 "9,015,416; 8,868,701; 8,583,769. Covers internet traffic management "
                 "and routing — a completely different patent family from the video "
                 "codec patents in Delaware, Virginia, and the ITC. Targets Amazon's "
                 "cloud infrastructure and streaming delivery platform. Entirely absent "
                 "from Part 1 analysis.",
    },
]

# ---------------------------------------------------------------------------
# CourtListener API functions
# ---------------------------------------------------------------------------

def fetch_docket_by_id(courtlistener_id: str, label: str) -> dict:
    """Fetch docket metadata from CourtListener by internal ID."""
    url = f"{BASE_URL}/dockets/{courtlistener_id}/"
    print(f"  Fetching: {label}")
    print(f"  URL: {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"  Success: {data.get('case_name', 'Unknown case name')}")
            return data
        else:
            print(f"  Warning: HTTP {response.status_code} for {label}")
            return {}
    except requests.RequestException as e:
        print(f"  Error fetching {label}: {e}")
        return {}


def fetch_docket_entries(courtlistener_id: str, label: str, max_entries: int = 10) -> list:
    """Fetch recent docket entries for a case."""
    url = f"{BASE_URL}/docket-entries/"
    params = {
        "docket": courtlistener_id,
        "order_by": "-date_filed",
        "page_size": max_entries,
    }
    print(f"  Fetching docket entries for: {label}")

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if response.status_code == 200:
            entries = response.json().get("results", [])
            print(f"  Found {len(entries)} recent entries")
            return entries
        else:
            print(f"  Warning: HTTP {response.status_code} for docket entries")
            return []
    except requests.RequestException as e:
        print(f"  Error fetching docket entries: {e}")
        return []


def search_docket_by_number(docket_number: str, court: str, label: str) -> dict:
    """Search CourtListener for a docket by case number and court."""
    url = f"{BASE_URL}/dockets/"
    params = {
        "docket_number": docket_number,
        "court": court,
    }
    print(f"  Searching for: {label} ({docket_number})")

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results:
                print(f"  Found: {results[0].get('case_name', 'Unknown')}")
                return results[0]
            else:
                print(f"  Not found in CourtListener: {docket_number}")
                return {}
        else:
            print(f"  Warning: HTTP {response.status_code}")
            return {}
    except requests.RequestException as e:
        print(f"  Error: {e}")
        return {}


# ---------------------------------------------------------------------------
# Build enriched fact section
# ---------------------------------------------------------------------------

def build_us_proceedings_section(cases: list, live_data: dict) -> str:
    """
    Builds a structured US proceedings section for the enriched input file.
    Combines known facts with any live CourtListener data retrieved.
    """
    lines = []
    lines.append("=" * 70)
    lines.append("US PROCEEDINGS — ENRICHED FACT LAYER")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("Source: CourtListener/PACER + verified public sources")
    lines.append("=" * 70)
    lines.append("")
    lines.append("IMPORTANT NOTE FOR AGENTS:")
    lines.append("The original JUVE Patent article referenced only the District of")
    lines.append("Delaware case (1:25-cv-01365) and omitted three additional US")
    lines.append("proceedings. The Delaware case is STAYED as a companion to the ITC")
    lines.append("investigation and carries NO independent coercive weight. The ITC")
    lines.append("investigation, Eastern District of Virginia case, and Western District")
    lines.append("of Texas case are the live US proceedings that matter strategically.")
    lines.append("")

    for i, case in enumerate(cases, 1):
        lines.append(f"US PROCEEDING {i}: {case['label']}")
        lines.append(f"Status: {case['status']}")
        lines.append(f"Docket: {case['docket_number']}")
        lines.append(f"Court: {case['court'].upper()}")
        lines.append("")
        lines.append("Known Facts:")
        lines.append(case['notes'])
        lines.append("")

        # Add any live CourtListener data if retrieved
        cl_data = live_data.get(case['label'], {})
        if cl_data:
            lines.append("Live CourtListener Data:")
            if cl_data.get('case_name'):
                lines.append(f"  Case Name: {cl_data['case_name']}")
            if cl_data.get('date_filed'):
                lines.append(f"  Date Filed: {cl_data['date_filed']}")
            if cl_data.get('date_terminated'):
                lines.append(f"  Date Terminated: {cl_data['date_terminated']}")
            if cl_data.get('assigned_to_str'):
                lines.append(f"  Assigned Judge: {cl_data['assigned_to_str']}")
            if cl_data.get('cause'):
                lines.append(f"  Cause of Action: {cl_data['cause']}")
            if cl_data.get('nature_of_suit'):
                lines.append(f"  Nature of Suit: {cl_data['nature_of_suit']}")

            entries = live_data.get(f"{case['label']}_entries", [])
            if entries:
                lines.append(f"  Recent Docket Entries ({len(entries)}):")
                for entry in entries[:5]:  # Show up to 5 most recent
                    date = entry.get('date_filed', 'Unknown date')
                    desc = entry.get('description', 'No description')
                    # Truncate long descriptions
                    if len(desc) > 150:
                        desc = desc[:150] + "..."
                    lines.append(f"    [{date}] {desc}")

        lines.append("-" * 50)
        lines.append("")

    lines.append("STRATEGIC SIGNIFICANCE SUMMARY FOR US/ITC AGENT:")
    lines.append("")
    lines.append("1. ITC 337-TA-3869 is the primary US lever. An exclusion order")
    lines.append("   blocks physical import of FireTV, Kindle, and Echo Show devices.")
    lines.append("   This is commercial disruption, not financial penalty.")
    lines.append("")
    lines.append("2. Eastern District of Virginia (2:25-cv-00822) is active and")
    lines.append("   covers a different patent set than the ITC/Delaware cases.")
    lines.append("   It runs on an independent timeline.")
    lines.append("")
    lines.append("3. Western District of Texas covers content delivery patents —")
    lines.append("   a completely different technology layer targeting Amazon's")
    lines.append("   cloud infrastructure, not just its devices.")
    lines.append("")
    lines.append("4. Delaware (1:25-cv-01365) is stayed and irrelevant as a")
    lines.append("   standalone pressure mechanism. Do not weight it.")
    lines.append("")
    lines.append("=" * 70)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------

def main():
    print("\n" + "=" * 60)
    print("InterDigital v Amazon — Part 2 US Docket Fetcher")
    print("=" * 60)

    # Read original JUVE article
    article_path = "inputs/juve_amazon_interdigital_article.txt"
    if not os.path.exists(article_path):
        raise FileNotFoundError(
            f"Original article not found at {article_path}. "
            "Please ensure the JUVE article is in the inputs/ folder."
        )

    with open(article_path, "r", encoding="utf-8") as f:
        original_article = f.read()

    print(f"\nLoaded original article: {len(original_article)} characters")

    # Fetch live CourtListener data
    print("\n--- Fetching live docket data from CourtListener ---")
    live_data = {}

    for case in US_CASES:
        print(f"\nProcessing: {case['label']}")

        if case['courtlistener_id']:
            # Fetch by known CourtListener ID
            docket_data = fetch_docket_by_id(
                case['courtlistener_id'],
                case['label']
            )
            if docket_data:
                live_data[case['label']] = docket_data

                # Also fetch recent docket entries
                entries = fetch_docket_entries(
                    case['courtlistener_id'],
                    case['label']
                )
                if entries:
                    live_data[f"{case['label']}_entries"] = entries

        elif case['court'] != 'itc' and case['docket_number'] != 'pending':
            # Try searching by docket number
            docket_data = search_docket_by_number(
                case['docket_number'],
                case['court'],
                case['label']
            )
            if docket_data:
                live_data[case['label']] = docket_data

        else:
            print(f"  Skipping CourtListener fetch (ITC or pending docket number)")
            print(f"  Using verified research data instead")

    # Build enriched US proceedings section
    print("\n--- Building enriched fact layer ---")
    us_proceedings_section = build_us_proceedings_section(US_CASES, live_data)

    # Compose enriched input file
    enriched_content = f"""INTERDIGITAL v AMAZON — PART 2 ENRICHED ANALYSIS INPUT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This file combines the original JUVE Patent article with enriched US
proceedings data pulled from CourtListener/PACER. The US proceedings
section corrects a material omission in the Part 1 analysis.

{'=' * 70}
ORIGINAL SOURCE ARTICLE (JUVE Patent, 16 March 2026)
{'=' * 70}

{original_article}

{us_proceedings_section}
"""

    # Write enriched input file
    output_path = "inputs/part2_enriched_input.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(enriched_content)

    print(f"\nEnriched input file written: {output_path}")
    print(f"Total length: {len(enriched_content):,} characters")

    # Save raw CourtListener data as JSON for reference
    json_path = "outputs/courtlistener_raw_data.json"
    os.makedirs("outputs", exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(live_data, f, indent=2, default=str)

    print(f"Raw CourtListener data saved: {json_path}")

    print("\n--- Next steps ---")
    print("1. Open main.py")
    print("2. Change article_path to: 'inputs/part2_enriched_input.txt'")
    print("3. Run: python -m app.main")
    print("\nPart 2 analysis ready to run.")
    print("=" * 60)


if __name__ == "__main__":
    main()
