"""Experiment 1 - plain word matching (TF-IDF + cosine similarity).
Ranks every requirement by how many (weighted) words it shares with the change text."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from common import tokens

NAME = "exp1_word_matching"


def rank(change, cands):
    ids = list(cands)
    vec = TfidfVectorizer(
        tokenizer=tokens, lowercase=False, token_pattern=None, sublinear_tf=True
    )
    m = vec.fit_transform([cands[i] for i in ids] + [change["query"]])
    sims = cosine_similarity(m[-1], m[:-1]).ravel()
    return [ids[i] for i in sims.argsort()[::-1]]
