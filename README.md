# Edit Scale vs Change Impact Analysis — experiment code

Research question: does the size of an edit to a requirement (minor vs major) change how
well tools find the other requirements it affects?

## 1. Setup (once)

```bash
pip install -r requirements.txt
```

## 2. Run

```bash
python src/fix_dataset.py      # rebuilds data/wasp/changes.json (already done, safe to re-run)
python run_all.py              # runs Experiments 1, 2 (and 3 if an API key is set)
```

Results are written to `results/summary.md` (tables for the paper) and
`results/per_change_results.csv` (every number, one row per change × tool).

## 3. What was fixed in the data

| Problem | Fix |
|---|---|
| C6 was missing from `changes.json` (6 changes in the original CSV, only 5 used) | Restored. It is a deletion that affects only 1 requirement. |
| IDs like `"R16 "` had trailing spaces | Trimmed |
| No old/new text, so edit size could not be computed | Each change now has `old_text`, `new_text`, `target_requirement` (our annotation, see `src/fix_dataset.py`) |
| Edit size and edit type were mixed up | Separate `change_type` field (modify / delete) |
| Top-5 recall punishes changes with many affected requirements | New main metric `norm_recall@k` = hits / min(k, number affected), plus AP and R-precision |

Correct counts: **72 requirements, 6 changes, 23 change–requirement pairs, 18 distinct affected requirements.**

## 4. The three experiments

| # | File | Method |
|---|---|---|
| 1 | `src/exp1_word_matching.py` | TF-IDF word matching + cosine similarity |
| 2 | `src/exp2_semantic.py` | Sentence embeddings (`all-MiniLM-L6-v2`). Falls back to LSA if the model can't download — the tool name then says `LSA-fallback`; don't report those as embedding results. |
| 3 | `src/exp3_llm.py` | Google Gemini scores every requirement 0–10 for the change (based on Etezadi et al., 2025). Needs a free Gemini API key. |

### Running Experiment 3 (Google Gemini)

1. Get a key at aistudio.google.com.
2. Windows (PowerShell):
   ```powershell
   $env:GEMINI_API_KEY="paste-your-key"
   python run_all.py
   ```
   Windows cmd: `set GEMINI_API_KEY=paste-your-key`. Mac/Linux: `export GEMINI_API_KEY=paste-your-key`.
   Default model is `gemini-2.5-flash`; change it with `GEMINI_MODEL` if you want.

Answers are cached in `results/llm_cache.json`, so re-runs are free and give the same numbers.

## 5. Other tools

- `python run_all.py --exclude C6` : results on the 5-change WASP benchmark used by Etezadi et al. (2025)
- `python src/labeller_agreement.py labels_A.csv labels_B.csv` : Cohen's kappa between the two people who label impact sets
- Figures for the paper/slides are saved in `results/figures/`
- `data/own_edits/candidate_edits.csv` : 30 drafted edits (15 minor, 15 major) **without impact labels** — label them yourselves

## 6. Adding your own edits (needed for the real study)

1. Copy `data/own_edits/edits_template.csv` to `data/own_edits/edits.csv`.
2. One row per edit. Remove the `#` example rows.
   - `target_requirement`: the requirement you edit (e.g. `R42`)
   - `old_text`: leave empty to use the current text of the target requirement
   - `new_text`: the edited wording; **leave empty for a deletion**
   - `change_type`: `modify` or `delete`
   - `change_description`: what the analyst would read (optional)
   - `impact_set`: affected requirement IDs separated by `;` — include the target itself, like WASP does
   - `human_label`: `minor` or `major` as judged by a person (used for RQ1)
3. `python run_all.py` picks the file up automatically.

Aim for ≥ 26 minor and ≥ 26 major edits, and make sure **both groups contain modify and delete
edits**. Otherwise you can't tell whether a difference comes from edit size or edit type.
