"""
==============================================================
  models/ml_model.py  —  ML Classification Model
==============================================================
  Two models available (same interface):
    • RandomForestClassifier   — robust, handles imbalance well
    • GradientBoostingClassifier — higher accuracy, slower train

  Both predict P(is_good_match=1) for a (user, job) pair.
  The probability is used as the ML score in the hybrid engine.

  Input features (from config.settings.NUMERIC_FEATURES):
    skill_match_score, location_match, salary_fit,
    experience_fit, job_type_match, interaction_score,
    experience_years

  Evaluation metrics tracked:
    Accuracy, AUC-ROC, Precision, Recall, F1-Score
==============================================================
"""

import os
import pickle

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score, roc_auc_score,
    classification_report, confusion_matrix,
)
from sklearn.preprocessing import StandardScaler

from config.settings import (
    MODEL_DIR,
    NUMERIC_FEATURES,
    TARGET_COLUMN,
    RANDOM_FOREST_PARAMS,
    GRADIENT_BOOST_PARAMS,
)
from utils.logger import get_logger

log = get_logger(__name__)

# ── Persisted file paths ──────────────────────────────────────
_RF_MODEL_FILE    = os.path.join(MODEL_DIR, "random_forest.pkl")
_GB_MODEL_FILE    = os.path.join(MODEL_DIR, "gradient_boost.pkl")
_SCALER_FILE      = os.path.join(MODEL_DIR, "feature_scaler.pkl")


# ─────────────────────────────────────────────────────────────
#  PUBLIC CLASS
# ─────────────────────────────────────────────────────────────

class JobMatchClassifier:
    """
    Trains Random Forest AND Gradient Boosting classifiers.
    Exposes a unified predict_proba() that uses the best model.

    Example:
        clf = JobMatchClassifier()
        clf.fit(interactions_df)
        prob = clf.predict_proba(feature_dict)
    """

    def __init__(self):
        # Both models are trained; best one used at inference
        self.rf_model  = RandomForestClassifier(**RANDOM_FOREST_PARAMS)
        self.gb_model  = GradientBoostingClassifier(**GRADIENT_BOOST_PARAMS)
        self.scaler    = StandardScaler()

        # Set after fit() — points to whichever model scored higher
        self.best_model = None
        self.best_name  = None

        log.info("JobMatchClassifier initialized (RF + GB)")

    # ──────────────────────────────────────────────────────────
    #  FIT
    # ──────────────────────────────────────────────────────────

    def fit(self, df: pd.DataFrame) -> dict:
        """
        Train both classifiers, evaluate, pick the best.

        Args:
            df: Full interactions DataFrame with feature columns.

        Returns:
            metrics dict with accuracy / AUC for both models.
        """
        log.info("Preparing features for ML training...")

        X, y = self._prepare_xy(df)

        # ── Train / test split (80/20, stratified) ────────────
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # ── Scale features (important for GB) ─────────────────
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled  = self.scaler.transform(X_test)

        # ── Train Random Forest ────────────────────────────────
        log.info("Training Random Forest...")
        self.rf_model.fit(X_train_scaled, y_train)
        rf_metrics = self._evaluate(self.rf_model, X_test_scaled, y_test, "Random Forest")

        # ── Train Gradient Boosting ────────────────────────────
        log.info("Training Gradient Boosting...")
        self.gb_model.fit(X_train_scaled, y_train)
        gb_metrics = self._evaluate(self.gb_model, X_test_scaled, y_test, "Gradient Boosting")

        # ── Pick best model by AUC ─────────────────────────────
        if gb_metrics["auc"] >= rf_metrics["auc"]:
            self.best_model, self.best_name = self.gb_model, "Gradient Boosting"
        else:
            self.best_model, self.best_name = self.rf_model, "Random Forest"

        log.info(f"Best model selected: {self.best_name} ✓")

        # ── Cross-validation on best model (5 folds) ──────────
        cv_scores = cross_val_score(
            self.best_model, X_train_scaled, y_train,
            cv=5, scoring="roc_auc"
        )
        log.info(
            f"5-fold CV AUC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}"
        )

        return {
            "random_forest"     : rf_metrics,
            "gradient_boosting" : gb_metrics,
            "best_model"        : self.best_name,
            "cv_auc_mean"       : round(cv_scores.mean(), 4),
            "cv_auc_std"        : round(cv_scores.std(), 4),
        }

    # ──────────────────────────────────────────────────────────
    #  PREDICT
    # ──────────────────────────────────────────────────────────

    def predict_proba(self, features: dict) -> float:
        """
        Predict probability that (user, job) is a good match.

        Args:
            features: Dict with keys matching NUMERIC_FEATURES.
                      Example:
                      {
                          "skill_match_score": 0.5,
                          "location_match"   : 1,
                          "salary_fit"       : 1,
                          "experience_fit"   : 1,
                          "job_type_match"   : 0,
                          "interaction_score": 4,
                          "experience_years" : 3,
                      }

        Returns:
            float probability in [0, 1]
        """
        self._assert_fitted()

        # Build a 1-row DataFrame in the correct column order
        row = pd.DataFrame([{k: features.get(k, 0) for k in NUMERIC_FEATURES}])
        row_scaled = self.scaler.transform(row)

        # predict_proba returns [[p_class0, p_class1]]
        prob = self.best_model.predict_proba(row_scaled)[0][1]
        return round(float(prob), 4)

    def get_feature_importance(self) -> pd.DataFrame:
        """
        Return feature importances from the best model as a
        sorted DataFrame (most important first).
        """
        self._assert_fitted()
        importances = self.best_model.feature_importances_
        return (
            pd.DataFrame({
                "feature"   : NUMERIC_FEATURES,
                "importance": importances,
            })
            .sort_values("importance", ascending=False)
            .reset_index(drop=True)
        )

    # ──────────────────────────────────────────────────────────
    #  SAVE / LOAD
    # ──────────────────────────────────────────────────────────

    def save(self) -> None:
        """Persist both models + scaler to disk."""
        self._assert_fitted()
        _dump(self.rf_model,  _RF_MODEL_FILE)
        _dump(self.gb_model,  _GB_MODEL_FILE)
        _dump(self.scaler,    _SCALER_FILE)
        log.info("JobMatchClassifier saved ✓")

    def load(self) -> "JobMatchClassifier":
        """Load persisted models from disk."""
        self.rf_model  = _load(_RF_MODEL_FILE)
        self.gb_model  = _load(_GB_MODEL_FILE)
        self.scaler    = _load(_SCALER_FILE)

        # Default best model to GB (can be overridden)
        self.best_model = self.gb_model
        self.best_name  = "Gradient Boosting"

        log.info("JobMatchClassifier loaded from disk ✓")
        return self

    def is_saved(self) -> bool:
        """Return True if all model files exist on disk."""
        return all(os.path.exists(f) for f in [
            _RF_MODEL_FILE, _GB_MODEL_FILE, _SCALER_FILE
        ])

    # ──────────────────────────────────────────────────────────
    #  PRIVATE
    # ──────────────────────────────────────────────────────────

    def _prepare_xy(self, df: pd.DataFrame):
        """
        Extract feature matrix X and label vector y from df.
        Missing values are filled with column mean.
        """
        X = df[NUMERIC_FEATURES].fillna(df[NUMERIC_FEATURES].mean())
        y = df[TARGET_COLUMN]
        log.info(
            f"Feature matrix: {X.shape} | "
            f"Class balance: {y.value_counts().to_dict()}"
        )
        return X.values, y.values

    def _evaluate(self, model, X_test, y_test, name: str) -> dict:
        """Run evaluation and log a classification report."""
        y_pred  = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        acc = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_proba)

        log.info(f"\n{'─'*50}\n{name} Results:")
        log.info(f"  Accuracy : {acc:.4f}")
        log.info(f"  AUC-ROC  : {auc:.4f}")
        log.info(f"\n{classification_report(y_test, y_pred)}")

        return {"accuracy": round(acc, 4), "auc": round(auc, 4)}

    def _assert_fitted(self) -> None:
        if self.best_model is None:
            raise RuntimeError(
                "JobMatchClassifier is not fitted. "
                "Call fit() or load() first."
            )


# ─────────────────────────────────────────────────────────────
#  PICKLE HELPERS
# ─────────────────────────────────────────────────────────────

def _dump(obj, path: str) -> None:
    with open(path, "wb") as f:
        pickle.dump(obj, f)


def _load(path: str):
    with open(path, "rb") as f:
        return pickle.load(f)
