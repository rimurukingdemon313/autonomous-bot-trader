"""Model families the research lab may fit: a DECLARED, finite set.

Each family is a trainable statistical estimator, implemented with numpy
only, so a validated artifact can be loaded where production runs without
adding a dependency there. Hyper-parameters are fixed per family and
recorded in the artifact. The lab does not search over them: a search
would be undeclared configurations.

- `ridge`    L2-regularised linear regression of realised R on standardised
             features (closed form).
- `logistic` L2-regularised logistic regression of P(R > 0) (Newton/IRLS);
             expected R = p * mean(win) - (1 - p) * mean(|loss|) from the fit.
- `knn`      the analogue method as a family: mean R of the k nearest
             training rows. It is the current system's estimator and serves
             as the baseline the other families must beat.

Not implemented: tree/boosting, time-series (ARIMA/GARCH) and Bayesian
families. `MODEL_FAMILIES` is the plug-in point; a new family is a new
declared entry, and it is counted like any other choice.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

MODELS_VERSION = "models-1.0.0"


@dataclass
class Standardiser:
    mean: np.ndarray
    std: np.ndarray

    @classmethod
    def fit(cls, X: np.ndarray) -> "Standardiser":
        m = np.nanmean(X, axis=0)
        s = np.nanstd(X, axis=0)
        return cls(m, np.where(s > 0, s, 1.0))

    def __call__(self, X: np.ndarray) -> np.ndarray:
        return (X - self.mean) / self.std


@dataclass
class Fitted:
    family: str
    params: dict = field(default_factory=dict)
    _predict: object = None

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self._predict(np.asarray(X, float))

    def to_json(self) -> dict:
        def conv(v):
            return v.tolist() if isinstance(v, np.ndarray) else v
        return {"family": self.family, "version": MODELS_VERSION, "params": {k: conv(v) for k, v in self.params.items()}}


def _clean(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    ok = np.all(np.isfinite(X), axis=1) & np.isfinite(y)
    return X[ok], y[ok]


def fit_ridge(X: np.ndarray, y: np.ndarray, alpha: float = 10.0) -> Fitted:
    X, y = _clean(np.asarray(X, float), np.asarray(y, float))
    st = Standardiser.fit(X)
    Z = st(X)
    b0 = float(y.mean())
    A = Z.T @ Z + alpha * np.eye(Z.shape[1])
    w = np.linalg.solve(A, Z.T @ (y - b0))
    return Fitted("ridge", {"alpha": alpha, "mean": st.mean, "std": st.std, "w": w, "b0": b0},
                  lambda Xn: st(Xn) @ w + b0)


def fit_logistic(X: np.ndarray, y: np.ndarray, alpha: float = 1.0, iters: int = 25) -> Fitted:
    X, y = _clean(np.asarray(X, float), np.asarray(y, float))
    st = Standardiser.fit(X)
    Z = np.hstack([np.ones((len(X), 1)), st(X)])
    t = (y > 0).astype(float)
    w = np.zeros(Z.shape[1])
    reg = alpha * np.eye(Z.shape[1])
    reg[0, 0] = 0.0
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-np.clip(Z @ w, -30, 30)))
        H = Z.T @ (Z * (p * (1 - p))[:, None]) + reg
        g = Z.T @ (p - t) + reg @ w
        step = np.linalg.solve(H, g)
        w -= step
        if np.max(np.abs(step)) < 1e-8:
            break
    win = float(y[y > 0].mean()) if (y > 0).any() else 0.0
    loss = float(-y[y <= 0].mean()) if (y <= 0).any() else 0.0

    def predict(Xn):
        Zn = np.hstack([np.ones((len(Xn), 1)), st(Xn)])
        p = 1.0 / (1.0 + np.exp(-np.clip(Zn @ w, -30, 30)))
        return p * win - (1 - p) * loss

    return Fitted("logistic", {"alpha": alpha, "mean": st.mean, "std": st.std, "w": w,
                               "mean_win": win, "mean_loss": loss}, predict)


def fit_knn(X: np.ndarray, y: np.ndarray, k: int = 100) -> Fitted:
    X, y = _clean(np.asarray(X, float), np.asarray(y, float))
    st = Standardiser.fit(X)
    Z = st(X)
    kk = min(k, len(Z))

    def predict(Xn):
        Q = st(Xn)
        out = np.full(len(Q), np.nan)
        for i, q in enumerate(Q):
            if not np.all(np.isfinite(q)):
                continue
            d = np.sum((Z - q) ** 2, axis=1)
            out[i] = float(y[np.argpartition(d, kk - 1)[:kk]].mean())
        return out

    # The fitted k-NN IS its training set; the artifact stores it (research only).
    return Fitted("knn", {"k": kk, "mean": st.mean, "std": st.std, "n_train": len(Z)}, predict)


MODEL_FAMILIES = {"ridge": fit_ridge, "logistic": fit_logistic, "knn": fit_knn}
