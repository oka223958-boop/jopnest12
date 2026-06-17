"""
==============================================================
  train.py  —  Model Training Pipeline
==============================================================
  Run this ONCE to train all models and save them to disk.
  After training, the Flask API loads the saved models and
  serves recommendations without retraining.

  Usage:
      python train.py

  What it does:
    1. Load dataset + build jobs/users cache
    2. Fit TF-IDF ContentBasedRecommender on jobs
    3. Train Random Forest + Gradient Boosting classifier
    4. Save all models to models/saved/
    5. Print evaluation metrics summary
==============================================================
"""

import time

from utils.data_loader import load_dataset, load_jobs, load_users
from models.content_model import ContentBasedRecommender
from models.ml_model import JobMatchClassifier
from models.hybrid_engine import HybridRecommendationEngine
from utils.logger import get_logger

log = get_logger(__name__)


def train() -> None:
    """
    Full training pipeline.
    Trains both models, evaluates, and saves to disk.
    """

    log.info("=" * 60)
    log.info("  JobNest Training Pipeline  —  Starting")
    log.info("=" * 60)

    start_time = time.time()

    # ── 1. Load Data ───────────────────────────────────────────
    log.info("\n[1/4] Loading dataset...")
    df    = load_dataset()
    jobs  = load_jobs(df)
    users = load_users(df)
    log.info(
        f"  Dataset : {df.shape[0]:,} rows\n"
        f"  Jobs    : {len(jobs):,} unique\n"
        f"  Users   : {len(users):,} unique"
    )

    # ── 2. Train Content-Based Model (TF-IDF) ─────────────────
    log.info("\n[2/4] Training TF-IDF Content Model...")
    content_model = ContentBasedRecommender()
    content_model.fit(jobs)

    # Quick sanity check: recommend for first user
    sample_user = users.iloc[0]
    sample_recs = content_model.recommend(sample_user, top_n=3)
    log.info(
        f"  Sanity check → top job for '{sample_user['user_name']}': "
        f"'{sample_recs.iloc[0]['title']}' "
        f"(score={sample_recs.iloc[0]['content_score']:.4f})"
    )

    # ── 3. Train ML Classifier ────────────────────────────────
    log.info("\n[3/4] Training ML Classifier (RF + GB)...")
    ml_model = JobMatchClassifier()
    metrics  = ml_model.fit(df)

    log.info("\n  ── Evaluation Summary ──────────────────────")
    for model_name in ["random_forest", "gradient_boosting"]:
        m = metrics[model_name]
        log.info(
            f"  {model_name:<22} | "
            f"Accuracy: {m['accuracy']:.4f} | "
            f"AUC-ROC: {m['auc']:.4f}"
        )
    log.info(
        f"\n  Best model  : {metrics['best_model']}\n"
        f"  CV AUC      : {metrics['cv_auc_mean']:.4f} ± {metrics['cv_auc_std']:.4f}"
    )

    # ── Feature importance ─────────────────────────────────────
    log.info("\n  Feature Importances:")
    fi = ml_model.get_feature_importance()
    for _, row in fi.iterrows():
        bar = "█" * int(row["importance"] * 100)
        log.info(f"  {row['feature']:<22} {bar:<30} {row['importance']:.4f}")

    # ── 4. Save All Models ────────────────────────────────────
    log.info("\n[4/4] Saving models to disk...")

    # Bundle into HybridEngine and save together
    engine = HybridRecommendationEngine()
    engine.content_model = content_model
    engine.ml_model      = ml_model
    engine.save()

    # ── Done ──────────────────────────────────────────────────
    elapsed = time.time() - start_time
    log.info("\n" + "=" * 60)
    log.info(f"  Training complete in {elapsed:.1f}s")
    log.info(f"  Models saved to: models/saved/")
    log.info(f"  Run:  python app.py  to start the API")
    log.info("=" * 60)


if __name__ == "__main__":
    train()
