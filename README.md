# Standards at Risk

Multi-agent AI analysis of SEP/FRAND patent disputes.
Companion code for the [Standards at Risk Substack](your-substack-url).

## InterDigital v Amazon

`interdigital_analysis.py` implements the six-agent, four-round reasoning
system described in the article. It uses Claude Sonnet 4.6 via the Anthropic API.

## Setup

pip install anthropic
export ANTHROPIC_API_KEY=your_key_here
python interdigital_analysis.py

## Note

The seed article in the file is abbreviated. Replace the `SEED_ARTICLE`
variable with the full JUVE Patent article text for a complete run, located here https://www.juve-patent.com/cases/interdigital-vs-amazon-a-chronology-of-the-escalation/

## Part 2: US Docket Enrichment and Corrected Analysis

Part 2 addressed a documented error in Part 1 — the stayed Delaware companion case
was incorrectly flagged as a live pressure lever — and added live PACER docket data
for all four US proceedings via the CourtListener API.

### What Changed

The seed document for Part 1 was the JUVE Patent chronology, which referenced only
one US case (the Delaware companion complaint) and omitted three others entirely.
Part 2 adds a pre-processing step that pulls live docket metadata for all identified
US proceedings before the swarm runs.

**The four US proceedings:**

- **Delaware 1:25-cv-01365** — STAYED. Companion to ITC 337-TA-3869. No
  independent coercive weight. Correctly excluded from pressure analysis in Part 2.

- **ITC Investigation 337-TA-3869** — ACTIVE. Primary US enforcement lever.
  Seeks exclusion order blocking import of FireTV, Kindle, and Echo Show. ALJ
  initial determination projected March–June 2027 on standard 15–18 month schedule.

- **Eastern District of Virginia 2:25-cv-00822** — ACTIVE. Four different video
  coding patents. Transferred from Alexandria Division. Assigned to Judge Arenda
  L. Wright Allen. Represented by McKool Smith PC.

- **Western District of Texas** — ACTIVE. Six content delivery patents acquired
  from Edgio Inc. bankruptcy by DRNC Holdings in January 2025 — seven months
  before Amazon filed in the UK. Targets Amazon's cloud infrastructure, not devices.

### The Edgio Acquisition

InterDigital acquired the Texas content delivery patents through subsidiary DRNC
Holdings from Edgio Inc.'s bankruptcy in January 2025 — seven months before Amazon
filed in the UK in August 2025. These are non-SEP patents covering internet traffic
management and routing. InterDigital has no organic presence in this technology area.
The acquisition predates the dispute, suggesting premeditated multi-front preparation
rather than reactive enforcement.

### New Pre-Processor

**`fetch_us_dockets.py`** — pulls live docket metadata from CourtListener/PACER
for the Delaware and Virginia cases. ITC and Texas cases included via verified public
sources. Writes `inputs/part2_enriched_input.txt`.

### Key Finding

The settlement window moved from Q4 2026 (Part 1) to late 2026 / early Q1 2027.
The ITC is a genuine lever but operates on a 2027 timeline, not 2026. The Texas
cloud infrastructure case is the most underreported variable in the dispute.
Confidence: 54%.

## Part 3: PTAB Validity Layer, Regulatory Flank, and Standards Essentiality

Part 3 expands the system to ten agents and adds two new data source pre-processors.

### New Agents

Three agents were added to the swarm for Part 3:

**PTAB/Validity Agent** — evaluates whether pending IPR petitions or reexaminations
could invalidate patents central to InterDigital's enforcement campaign before key
litigation milestones. Models the PTAB institution environment under Director Squires
(institution rates below 40% as of December 2025), the Dolby IPR against InterDigital
US 9,185,268, and the Unified Patents reexamination of US 10,805,610.

**Regulatory/Competition Agent** — evaluates Article 102 TFEU exposure from
InterDigital's multi-forum enforcement posture and the Edgio patent acquisition pattern.
Models the EC notification (24 December 2025), Amazon's abuse-of-dominance claim
at the UK High Court, and whether pre-dispute acquisition of non-SEP patents against
a specific counterparty constitutes improper conduct under EU competition law.

**Standards Essentiality Agent** — evaluates the essentiality boundary under the ITU
Common Patent Policy for ITU-T/ITU-R/ISO/IEC. Models the "would be required to
implement" threshold, the encoder/decoder distinction in HEVC and related codec
standards, the internal decode loop question, and the legal vulnerability of HDR patents
as a dual-side patent family.

### New Pre-Processors

**`fetch_us_dockets.py`** — pulls live docket data from CourtListener/PACER for all
four US proceedings: the stayed Delaware companion case (1:25-cv-01365), the active
Eastern District of Virginia case (2:25-cv-00822), ITC Investigation 337-TA-3869,
and the Western District of Texas content delivery case. Writes
`inputs/part2_enriched_input.txt`.

**`fetch_ptab_data.py`** — queries the USPTO Open Data Portal PTAB API for IPR
petitions and reexaminations against InterDigital's asserted patents. Combines PTAB
data with Part 2 enriched input and writes `inputs/part3_enriched_input.txt`.

### Run Order

```bash
# Part 2 — US docket enrichment
python fetch_us_dockets.py

# Part 3 — PTAB enrichment (requires Part 2 output)
python fetch_ptab_data.py

# Run the swarm (point main.py at the desired input file)
python -m app.main
```

### API Keys Required

### A Note on DNS

The USPTO ODP API (`api.uspto.gov`) may not resolve on some home or corporate
routers. If you encounter DNS resolution errors, switching to Google's public DNS
servers (8.8.8.8 / 8.8.4.4) resolves the issue on most systems.

### Cost and Runtime (Part 3)

57 API calls across ten agents, five rounds, coverage audit, and final refinement.
Approximately $3.50 at current Claude Sonnet 4.6 pricing. Runtime approximately
seven minutes on a standard laptop.
