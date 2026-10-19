"""Experiment 2 - search based on meaning (sentence embeddings).
Uses the sentence-transformers model 'all-MiniLM-L6-v2' (downloads ~90 MB the first time).

If the model cannot be loaded (no internet / package missing) it falls back to LSA
(TF-IDF + SVD), which is only a rough stand-in for meaning. The output name then says
'LSA-fallback' so you never report fallback numbers as embedding results by mistake."""

import numpy as np

from common import tokens

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
NAME = "exp2_semantic"
_model = None
_cache = {}


def _load():
    global _model, NAME
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer(MODEL_NAME)
        except Exception as e:  # noqa: BLE001
            print(
                f"[exp2] Could not load {MODEL_NAME} ({type(e).__name__}). Using LSA fallback."
            )
            _model = "lsa"
            NAME = "exp2_semantic_LSA-fallback"
    return _model


def _embed(texts):
    m = _load()
    if m == "lsa":
        raise RuntimeError
    key = tuple(texts)
    if key not in _cache:
        _cache[key] = m.encode(list(texts), normalize_embeddings=True)
    return _cache[key]


def _lsa_rank(change, cands, ids):
    from sklearn.decomposition import TruncatedSVD
    from sklearn.feature_extraction.text import TfidfVectorizer

    docs = [cands[i] for i in ids] + [change["query"]]
    x = TfidfVectorizer(
        tokenizer=tokens, lowercase=False, token_pattern=None
    ).fit_transform(docs)
    z = TruncatedSVD(
        n_components=min(30, x.shape[1] - 1), random_state=0
    ).fit_transform(x)
    z /= np.linalg.norm(z, axis=1, keepdims=True) + 1e-12
    return z[-1] @ z[:-1].T


def rank(change, cands):
    ids = list(cands)
    if _load() == "lsa":
        sims = _lsa_rank(change, cands, ids)
    else:
        req_vecs = _embed(tuple(cands[i] for i in ids))
        q = _embed((change["query"],))[0]
        sims = req_vecs @ q
    return [ids[i] for i in np.argsort(-sims)]
