# Results summary

Changes: 6 (6 WASP, 0 own). Major = edit size >= 0.30. Tools: exp1_word_matching, exp2_semantic, exp3_llm_gemini.

## The changes

| Change | Type | Edit size | Group | Affected (n) |
|---|---|---|---|---|
| C1 | modify | 0.11 | minor | 2 |
| C2 | delete | 0.10 | minor | 9 |
| C3 | modify | 0.17 | minor | 1 |
| C4 | modify | 0.16 | minor | 1 |
| C5 | delete | 1.00 | major | 9 |
| C6 | delete | 0.05 | minor | 1 |

## RQ1 - Does the edit-size score agree with human judgement?

Not enough hand labels yet. Fill the `human_label` column (minor/major) in data/own_edits/edits.csv. Also have the two reviewers label separately and report their agreement with each other.

## Overall comparison of the three methods (all changes)

Existing method = Exp 1 word matching (baseline). Proposed = Exp 2 semantic, Exp 3 LLM.

| Method | n | precision@5 | recall@5 | F1@5 | norm_recall@5 | recall@10 | MAP |
|---|---|---|---|---|---|---|---|
| exp1_word_matching | 6 | 0.37 | 0.71 | 0.38 | 0.82 | 0.83 | 0.79 |
| exp2_semantic | 6 | 0.50 | 0.85 | 0.50 | 1.00 | 0.93 | 0.94 |
| exp3_llm_gemini | 6 | 0.47 | 0.69 | 0.44 | 0.83 | 0.96 | 0.52 |

## RQ2 - Do tools miss more affected requirements for major edits?

Main metric: **norm_recall@k** (fair to big impact sets). Plain recall@k shown for comparison.

| Tool | Group | n | recall@5 | norm_recall@5 | recall@10 | norm_recall@10 | AP |
|---|---|---|---|---|---|---|---|
| exp1_word_matching | minor | 5 | 0.79 | 0.86 | 0.91 | 0.91 | 0.84 |
| exp1_word_matching | major | 1 | 0.33 | 0.60 | 0.44 | 0.44 | 0.51 |
| exp2_semantic | minor | 5 | 0.91 | 1.00 | 0.93 | 0.93 | 0.95 |
| exp2_semantic | major | 1 | 0.56 | 1.00 | 0.89 | 0.89 | 0.89 |
| exp3_llm_gemini | minor | 5 | 0.71 | 0.80 | 0.96 | 0.96 | 0.43 |
| exp3_llm_gemini | major | 1 | 0.56 | 1.00 | 1.00 | 1.00 | 0.99 |

Statistical test (Mann-Whitney U, two-sided) and 95% bootstrap CI of the difference (major minus minor):

- exp1_word_matching / norm_recall@5: skipped (minor n=5, major n=1; need >= 3 each)
- exp1_word_matching / norm_recall@10: skipped (minor n=5, major n=1; need >= 3 each)
- exp1_word_matching / AP: skipped (minor n=5, major n=1; need >= 3 each)
- exp2_semantic / norm_recall@5: skipped (minor n=5, major n=1; need >= 3 each)
- exp2_semantic / norm_recall@10: skipped (minor n=5, major n=1; need >= 3 each)
- exp2_semantic / AP: skipped (minor n=5, major n=1; need >= 3 each)
- exp3_llm_gemini / norm_recall@5: skipped (minor n=5, major n=1; need >= 3 each)
- exp3_llm_gemini / norm_recall@10: skipped (minor n=5, major n=1; need >= 3 each)
- exp3_llm_gemini / AP: skipped (minor n=5, major n=1; need >= 3 each)

### Sensitivity: does the answer change with the cut-off? (norm_recall@5, major minus minor)

| Tool | 0.20 | 0.25 | 0.30 | 0.35 | 0.40 | 0.45 | 0.50 |
|---|---|---|---|---|---|---|---|
| exp1_word_matching | -0.26 (5/1) | -0.26 (5/1) | -0.26 (5/1) | -0.26 (5/1) | -0.26 (5/1) | -0.26 (5/1) | -0.26 (5/1) |
| exp2_semantic | +0.00 (5/1) | +0.00 (5/1) | +0.00 (5/1) | +0.00 (5/1) | +0.00 (5/1) | +0.00 (5/1) | +0.00 (5/1) |
| exp3_llm_gemini | +0.20 (5/1) | +0.20 (5/1) | +0.20 (5/1) | +0.20 (5/1) | +0.20 (5/1) | +0.20 (5/1) | +0.20 (5/1) |

(numbers in brackets = minor/major group sizes)

### By change type (modify vs delete), norm_recall@5

| Tool | delete (n) | modify (n) |
|---|---|---|
| exp1_word_matching | 0.80 (3) | 0.83 (3) |
| exp2_semantic | 1.00 (3) | 1.00 (3) |
| exp3_llm_gemini | 1.00 (3) | 0.67 (3) |

## RQ3 - Does the amount of rewritten text predict how many requirements are affected?

Spearman rho (edit size vs number affected) = 0.15, p = 0.770, n = 6.

- delete: mean affected = 6.33 (n = 3)
- modify: mean affected = 1.33 (n = 3)

_With fewer than ~20 changes per group these numbers are a pilot only; do not claim significance from WASP alone._