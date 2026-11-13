# Sovereign Green Bond Pricing: Evidence from German Twin Bonds

Replication code and aggregate research outputs for a German sovereign green-bond contractual-twin validation study. This is a working research repository, not a journal acceptance or a claim of universal model superiority.

## Main benchmark

The final comparison uses 8,872 common pair-days, ten contractual twins, and identical eligible training universes across five comparator methods. The conventional twins are withheld from all reconstructed comparator methods. Pair-balanced mean absolute reconstruction errors (basis points) are:

| Method | MAE |
|---|---:|
| Nearest maturity | 3.755206 |
| Maturity interpolation | 2.039766 |
| Nearest duration | 3.195121 |
| Duration interpolation | 1.858458 |
| Cash-flow NSS | 2.585741 |

The nearest-maturity minus duration-interpolation difference is 1.896748 bp, with a three-month calendar-block bootstrap 95% interval of [1.640606, 2.136684] bp. This is an error-reduction result relative to recorded twin yields, not a causal estimate of investor preferences or environmental impact. NSS performs better on some sign-preservation criteria.

## Contents and data rights

- `lseg_resume/`: public-source acquisition, parsing, contractual-term repair, duration, cash-flow NSS, and final harmonized-comparison code.
- `lseg_resume/bundesbank_official/`: source URLs/hashes and aggregate final outputs only.
- `figures/`: figure-generation code, three figures in PNG/PDF/SVG, and their aggregate plotting data.
- `validation/`: verification scope and results.

**No licensed LSEG observations, authentication credentials, manuscript, supplement, raw source workbooks, downloaded issuer HTML, or row-level source/derived panels are included.** LSEG is not required to run the public-source benchmark. Source manifests retain the original provenance; their hashes describe externally obtained input snapshots, not files bundled in this repository. Third-party rights remain with the original providers. No open-source license is granted by this repository; a publication/reuse license should be selected by the author separately.

## Reproduction

Use Python 3.12 in an isolated environment and install `requirements.txt`. Run all commands from the repository root. Fetch the Bundesbank monthly workbooks listed in `sources.json` and issuer factsheets listed in `terms_manifest.json` directly from their providers, subject to applicable terms. Use the frozen listed URLs and compare SHA-256 hashes when reconstructing the study snapshot; a live refresh may change inputs. The included fetch scripts provide optional discovery/refresh, not a guarantee of an immutable snapshot.

```sh
python -m pip install -r requirements.txt
python lseg_resume/fetch_bundesbank.py
python lseg_resume/parse_bundesbank_twins.py
python lseg_resume/fetch_official_terms.py
python lseg_resume/repair_terms.py
python lseg_resume/twin_matching_benchmark.py
python lseg_resume/twin_duration_verified.py
python lseg_resume/cashflow_nss_verified.py
python lseg_resume/fair_shared_universe.py
python figures/build_figures.py
```

Cash-flow fitting is computationally intensive. `twin_matching_benchmark.py` and the intermediate duration outputs are dependencies, **not** the final comparable-method results. Only `fair_shared_*` results use the final harmonized training and observation sample. Figure scripts require the reconstructed `fair_shared_common_sample.parquet`, which is intentionally not distributed here.

## Methodological limits

The study uses TARGET T+2 settlement and a screened approximate cash-flow convention, with nominal payment dates not business-day adjusted. It is not a dealer-exact valuation library. The price reconstruction screen and contractual-term checks limit but do not eliminate convention risk. The sample is German sovereign twins over November 2020–October 2026; conclusions should not be generalized automatically to corporate or other sovereign green bonds. Bootstrap draws lacking any twin are excluded and the retained count is reported. Sign disagreement uses reference-eligible observations as its denominator; `both_outside_rate` is a distinct conditional sensitivity measure.

## Current verification

See `validation/REPORT.md`. Code compilation, regeneration of all three figures from the existing public-data analysis snapshot, and the final harmonized-stage rerun are checked separately. A clean network-to-final full pipeline has not been rerun during GitHub preparation.
