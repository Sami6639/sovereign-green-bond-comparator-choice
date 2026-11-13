# Repository preparation validation

Current author-selected title: *Sovereign Green Bond Pricing: Evidence from German Twin Bonds*.

Checked on 13 November 2026 against the delivered manuscript (previous title: *Sovereign Green Bond Pricing and Comparator Choice*) and the accompanying revised replication archive. The title update does not change the analyses or validation results.

- Compiled all nine Python scripts successfully.
- Reran the final harmonized comparator stage using the existing frozen public-data intermediate panels. MAE metrics, sign-disagreement statistics, and leave-one-twin-out results matched the supplied outputs (numeric tolerance 1e-12). Bootstrap output matched exactly.
- Confirmed 8,872 common rows, ten twins, 1,491 dates, and no duplicate twin-date keys.
- Regenerated all three figures successfully in PNG, PDF and SVG.
- The manuscript's benchmark size and reported MAE values agree with the checked outputs.
- Scanned the curated text/code for recognizable secret formats and manually reviewed source scripts for credentials. No credentials found.
- Excluded licensed LSEG observations, raw/row-level data, source HTML, manuscript and supplement, unrelated exploratory research notes, and obsolete comparisons.

## Limits

This preparation did not rerun the entire network-to-results pipeline. The original public-source parsing, duration calculation and expensive cash-flow NSS refit were not rerun. No claim is made that external source websites or layouts remain stable. Exact re-creation requires the frozen source versions identified in the source/hash manifests; live downloading may return changed content. Upstream code and assumptions are supplied for inspection, not certified as dealer-exact bond valuation.

Raw-data redistribution rights were not established, so raw files and row-level panels are not uploaded. Their absence means the final analysis and figures cannot be rerun from this repository alone without obtaining/reconstructing the inputs. Included aggregate results and plotting summaries remain inspectable.
