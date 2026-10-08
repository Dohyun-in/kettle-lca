# Factory-gate carbon footprint of one packaged BC1 1 L plastic electric kettle

Independent run `independent-uslci-commons-merged-2026-10-08`, study date 2026-10-08. Public alias: unset. Repository URL: not published yet. This file does not contain a commit SHA; record `git rev-parse HEAD` after the commit that adds this README.

The calculated climate result is partial. It is **2.93482020509481 kg CO2-eq** per packaged kettle for the matched inputs only. Unmatched inputs are omitted. They are not zeroes.

## 1. Study identity and purpose

- Title: Factory-gate carbon footprint of one packaged BC1 1 L plastic electric kettle.
- Public alias: unset. Full name and email are for the submission form, not this file.
- Run: independent. No revised run yet. No Git tag yet.
- Goal: build a reproducible matrix calculation for the shared kettle BOM, using Federal LCA Commons background data, and record every match and gap.
- Intended comparison: classmate totals and contributors, then one later modeling change kept separate from this run.

## 2. Product, declared unit and system boundary

Declared unit: one manufactured and packaged BC1 1 L plastic electric kettle at the factory gate. BC1 is the EU representative base case, not a named product.

BOM source: EU Electric Kettles preparatory study (2020), Task 4, Tables 4-3, 4-4 and 4-8. Local file: `data/bom.csv`.

Mass check passed: kettle 723.00 g, packaging 137.80 g, total 860.80 g.

Included: materials, the matched conversion processes, assembly only where a background process already contains it, and packaging. Excluded: customer delivery, use, and end of life. No use-phase or end-of-life extension is added to this factory-gate result.

Geography: the product definition is European. Background processes are United States or Northern America, as published. Reference year of the BOM is 2020. Background years are the years stored on each process.

Cut-offs that are reported rather than filled in: brass, copper metal, nylon, POM, polycarbonate, silicone, final assembly electricity, and any product or waste exchange whose provider is absent.

## 3. Foreground inventory and quantitative assumptions

Parameters live in `config/assumptions.yaml`.

| Parameter | Value | Unit | Evidence | Status |
| --- | --- | --- | --- | --- |
| Finished mass of each BOM line | see `data/bom.csv` | g | EU preparatory study, 2020 | sourced |
| Extra manufacturing loss on top of a matched process | 0 | fraction | BOM has no yield. A conversion process is used as published, including its own resin input. | assumed |
| PP injection molding resin input | 1.034 per 1 kg part, inside the dataset | kg/kg | USLCI injection-molding process | sourced, inside background |
| Corrugated board inside PP injection molding | 0.1 per 1 kg part | kg/kg | same process | sourced, inside background |
| Final assembly electricity | not calculated | kWh | BOM does not state it | unknown |
| Inbound transport added in the foreground | none | — | transport already inside a unit process is kept | assumed |
| Customer delivery, use, end of life | excluded | — | class boundary | sourced |
| Nylon grade | unspecified; no physical nylon process selected | — | BOM | unknown |
| Price-based USEEIO bridges | recorded, not used in the total | USD | Commons Merged bridge processes have no provider here | not calculated |

Finished mass in grams is divided by 1000 and demanded in the reference unit of the matched process. For every selected process that unit is kg. No second loss factor is applied, so resin already counted inside injection molding is not added again as a separate BOM line.

Final assembly electricity is left out. It is not entered as 0 kWh.

## 4. Background data and matching decisions

Database: Federal LCA Commons, repository `Federal_LCA_Commons/commons_merged`, which connects USLCI v1.2026-09.0 to external electricity providers. Local zip SHA-256: `ae9590f473fc7466a5167dfcbbb6e500a8bb939819f7eab9aaf86a68b411ee22`. The zip is not committed. Retrieval date: 2026-10-08. Manifest: `results/data_manifest.json`.

Full candidate list: `results/candidates.csv`. Accepted rows: `results/mapping_table.csv`.

Browse URL pattern: `https://www.lcacommons.gov/lca-collaboration/Federal_LCA_Commons/commons_merged/dataset/PROCESS/{uuid}`.

| Input | Dataset | UUID | Version | Geography | Reference demand |
| --- | --- | --- | --- | --- | --- |
| Stainless steel, 186 g | Steel; stainless 304; flat rolled coil | `49f5324b-fc33-36e9-b5af-3c80d73492bd` | 00.01.014 | Northern America | 0.186 kg |
| PP, 350.25 g | Injection molding; rigid polypropylene part; at plant | `89a2b59a-1ca2-34f5-acc8-a8eaaa6fa870` | 00.00.022 | United States | 0.35025 kg |
| PVC, 43.50 g | Polyvinyl chloride resin, PVC; suspension grade; at plant | `3dbccdda-2014-4239-ad1f-4e15c034942b` | 00.01.015 | United States | 0.0435 kg |
| ABS, 30.00 g | Acrylonitrile-butadiene-styrene, ABS; copolymer resin; at plant | `0e42a306-ee2d-362e-8bc3-580000096459` | 00.01.010 | Northern America | 0.03 kg |
| LDPE foil, 6.30 g | Low-density polyethylene, LDPE; virgin resin; at plant | `6a12cba1-889d-4515-90f8-89feb8d662f2` | 00.01.012 | Northern America | 0.0063 kg |
| Cardboard, 131.50 g | Corrugated product; average production; at mill | `226ed3c2-e020-4c95-b1fc-4559fc2d18ac` | 00.01.008 | United States | 0.1315 kg |

Selection rules:

- Virgin, not recycled, because the kettle is a new product. Recycled alternatives stay in `results/candidates.csv`.
- PP uses injection molding, which already consumes 1.034 kg of virgin resin per kg of part. The resin process is not added again.
- PVC uses suspension-grade resin. Landfilling and roofing membranes were rejected. Cable extrusion was not found.
- LDPE foil uses LDPE resin. LLDPE stretch film was rejected because it is a different polymer. Foil conversion was not found.
- Cardboard uses average corrugated board. The 100% recycled board is kept as a later comparison candidate.
- Stainless steel uses 304 flat-rolled coil rather than quarto plate.

Not matched, so not given a climate number:

| Input | Mass (g) | What was found | Why it is not in the total |
| --- | ---: | --- | --- |
| Brass | 20.25 | no process | no brass dataset |
| Copper | 15.00 | USEEIO bridge only | monetary proxy, provider absent |
| Nylon, grade unspecified | 49.50 | Nylon 6 and Nylon 66 USEEIO bridges | physical inventory absent |
| POM | 9.75 | no process | no acetal dataset |
| Polycarbonate | 6.75 | USEEIO bridge | monetary proxy, provider absent |
| Silicone | 12.00 | no process | no silicone dataset |

Monetary proxies, not used: Nylon 6 bridge `a2174501-418e-4b2e-9dbd-fa81f5f0bcc7` links 1 kg to 1.649258065 USD of Plastics with no provider. Polycarbonate bridge `531f7547-3175-4114-842a-cf358fb4a10b` links 1 kg to 6.970610088 USD of Plastics. Copper bridge `f0810c41` is not the copper-metal process; the storage bridge prices 1 kg at 9.13 USD of “Copper, gold and silver concentrates”. Price year and purchaser-versus-basic price are not stated on those exchanges, so they are not converted to impacts. The full bridge list is in `results/result.json` under `monetary_proxies_not_used`.

TianGong: not retrieved in this run. No local CLI session was available. Search code is `kettle_lca/tiangong.py`. A later run can add those matches without overwriting this result file.

Direct overlap: the PP injection-molding process consumes 0.1 kg of the same average corrugated-board process per 1 kg of molded part. For 0.35025 kg of PP part that is 0.035025 kg of board inside the PP result, in addition to the 0.1315 kg retail box. These are two demands for the same background process, not the same physical box entered twice.

## 5. Calculation and impact-assessment methods

The linked unit-process system uses one column per process and one row per process. The diagonal is the reference exchange. A product or waste input with a default provider is written on that provider’s row, after conversion into the provider’s reference unit. Outputs are positive and inputs are negative.

Then `A s = f`, `g = B s`, and `h = C g`, solved with `numpy.linalg.solve` rather than an explicit inverse. `f` is the finished mass of each matched material. Contributions are separate solves for each material. Their sum equals the total to numerical noise (difference about 10^-14 kg CO2-eq).

Software: Python 3.13, NumPy. Code: `kettle_lca/`.

Allocation: attributional. No recycling credit and no system expansion. Waste exchanges without a provider stay in `results/unresolved_links.csv` and are not given a climate value.

Impact method: IPCC AR6-100 shipped in the same zip, category `a6206006-65bc-395c-8dc9-f12262f45a04`, reference unit kg CO2-eq, version 01.04.001. Time horizon: 100 years. Fossil CO2 factor 1, fossil methane 29.8, biogenic methane 27.0, nitrous oxide 273. Biogenic CO2 to air is characterized as 0. That published zero is kept. Flows with no factor are listed in `results/uncharacterized_flows.csv` and are not added as zero. Most of those 3281 rows are elementary flows outside the climate category, such as water and minerals.

This run linked 1008 processes. It recorded 1608 exchanges with no usable provider (841 waste, 767 product) and 6 provider ids whose reference flow could not be read. Foreground product gaps are small: colorant in PP molding (0.0194 kg per kg part), a trace of polyvinyl acetate in PVC, and trace coating and adhesive in corrugated board. Larger unresolved exchanges sit deeper in background processes such as ethanol and irrigation. They are gaps in the characterized total.

## 6. How to reproduce the analysis

| Path | Role |
| --- | --- |
| `data/bom.csv` | Shared bill of materials |
| `config/study.yaml`, `config/assumptions.yaml` | Boundary and assumptions |
| `kettle_lca/` | Calculation |
| `results/` | This independent run |
| `docs/decisions.md`, `docs/prompt_log.md` | Human and assistant choices |

Runtime used here: macOS, Python 3.13. Dependencies: `requirements.txt` (NumPy 2.3.3, PyYAML 6.0.2, requests 2.32.5).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATA_GOV_API_KEY=your_own_key
python -m kettle_lca.fetch_commons
python -m kettle_lca
python -m pytest tests
```

`DATA_GOV_API_KEY` is a free data.gov key. The value is not stored in the repository. The zip is written to `data/cache/commons_merged.zip`, which is gitignored. Expected outputs are the files in `results/`. Open `results/result.json` and `results/contributions.csv`.

TianGong, if used later, needs a local browser login and does not take a password in the command:

```bash
npx --yes @tiangong-lca/cli@0.1.21 auth login
```

This environment had Node 22. The CLI documents Node 24.19.0. No TianGong records were retrieved.

Tests cover the Suh and Heijungs electricity–coal example (0.0175 kg CO2 per kWh in that fictitious system), unit conversion, and the BOM mass totals. They do not re-download the database.

## 7. Results, checks and interpretation

Calculation status: **partial**.

Characterized GWP100: **2.93482020509481 kg CO2-eq** per packaged kettle. This is the baseline for Commons Merged and IPCC AR6-100. It is not a complete factory-gate total.

| Contributor | Mass (g) | GWP100 (kg CO2-eq) |
| --- | ---: | ---: |
| Stainless steel, 304 flat-rolled coil | 186.00 | 1.4778044501722127 |
| PP injection-molded part | 350.25 | 1.0506386859396128 |
| Cardboard, average corrugated board | 131.50 | 0.2744351858298825 |
| PVC suspension resin | 43.50 | 0.06308827395127575 |
| ABS copolymer resin | 30.00 | 0.05534524819896836 |
| LDPE virgin resin | 6.30 | 0.013508361002842138 |
| Brass, copper, nylon, POM, PC, silicone | 113.25 | not calculated |

Top three characterized contributors: stainless steel, polypropylene molding, cardboard.

Signed biogenic CO2 inventory across the characterized system: 0.0016264296367671312 kg. It is characterized with the published factors, including zeros, and is not an extra number to add on top of the total.

Checks:

- BOM mass: pass, 723.00 + 137.80 = 860.80 g.
- Contribution sum: pass. The six contributions add to the reported total within about 10^-14 kg CO2-eq.
- Supplier closure: fail as a complete closure. 1608 exchanges have no usable provider. The six matched foreground processes themselves are present.
- Double counting: the PP process already includes 0.1 kg corrugated board per kg part. That board is also the retail-box process. See section 4.
- Unmatched mass, 113.25 g of 860.80 g, has no climate contribution in this total. Omitting it makes the total lower than a complete inventory. It is not a zero contribution.

The characterized result is driven by stainless coil and by polypropylene, including the resin, electricity, and other inputs inside injection molding. The European kettle is represented with US background data. That geography mismatch can move the total relative to a European database. Assembly electricity, nylon, metals other than stainless steel, POM, polycarbonate, and silicone are missing. A comparison that treats 2.93 kg CO2-eq as the full footprint is not supported.

## 8. Uncertainty and sensitivity

Uncertainty was not calculated. No distributions, draws, or seed were defined. The class comparison can still separate this partial parameter result from a later provider or method scenario. Variability between repeated assistant runs was not simulated.

## 9. Codex and human decisions

The calculation was assembled in Cursor. The assistant identified in this session is Grok 4.7. Codex model settings, temperature, and a Codex run id are unknown because Codex was not the tool that produced this run.

Decisions kept by the human owner of the repository, and the defaults used when they were not yet specified, are listed in `docs/decisions.md`. The prompt record is `docs/prompt_log.md`. Private chat text, contact details, and credentials are omitted.

The human still needs to set the public alias, review the matches, and decide whether a later run changes one choice.

## 10. Independent and revised runs

This directory’s `results/` files are the independent run. Do not overwrite them after seeing other students’ answers. No revised run has been made, so the revision comparison is not applicable.

A reserved one-change comparison, not executed here, is to replace average corrugated board with `Corrugated product; 100% recycled; at mill` (`9c10be0f-e38e-4551-b8b5-eef65fa27dcc`) and report the original total, the revised total, and the difference beside this baseline.
