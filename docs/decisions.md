# Decisions for the independent run

Study date: 2026-10-08. Run id: `independent-uslci-commons-merged-2026-10-08`.

## Kept for this baseline

- Factory gate only. Delivery, use, and end of life are excluded.
- Background database is Federal LCA Commons `commons_merged`, so USLCI electricity bridges can be followed. USLCI alone was not used as the calculation database.
- Impact method is the IPCC AR6-100 category shipped in that zip.
- Finished BOM mass is the demand. No extra scrap rate is applied on top.
- Where a part-manufacturing process exists and already contains the resin, that process is the match. Polypropylene uses injection molding, not molding plus a second resin demand.
- Virgin routes are preferred to recycled routes.
- Monetary USEEIO bridges are recorded and left out of the total.
- Missing inputs stay missing. They are not coded as zero.
- Final assembly electricity stays unknown.

## Not chosen, and why

- LLDPE stretch film for the LDPE foil: different polymer.
- PVC landfilling or roofing membrane: outside the factory-gate part.
- 100% recycled corrugated board: saved as the one-change revision, not the baseline.
- Copper sulfate as the copper part: wrong product.
- Nylon 6 monetary bridge as a physical inventory: the Plastics sector provider is not in this repository.

## Human review still open

- Public alias.
- Whether the US background is acceptable for the EU kettle.
- Whether the 0.1 kg of corrugated board inside PP molding should stay.
- The single change for a revised run, if one is made.
