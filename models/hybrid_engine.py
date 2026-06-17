"""
        content_candidates = self.content_model.recommend(user, top_n=50)

        # ── Step 2: ML scoring of candidates ──────────────────
        ml_scores = self._score_with_ml(user, content_candidates)
        content_candidates = content_candidates.copy()
        content_candidates["ml_score"] = ml_scores

        # ── Step 3: Hybrid score (weighted combination) ────────
        content_candidates["final_score"] = (
            CONTENT_WEIGHT * content_candidates["content_score"] +
            ML_WEIGHT      * content_candidates["ml_score"]
        ).round(4)

        # ── Step 4: Apply chatbot filters, sort and return top-N ──
        if jobs is not None and len(jobs) < len(self.content_model.jobs_ref):
            allowed_ids = set(str(i) for i in jobs["job_id"].tolist())
            mask = content_candidates["job_id"].apply(lambda x: str(x) in allowed_ids)
            filtered_candidates = content_candidates[mask]
            if not filtered_candidates.empty:
                content_candidates = filtered_candidates

        result = (
            content_candidates
            .sort_values("final_score", ascending=False)
            .head(top_n)
            .reset_index(drop=True)
        )

        log.info(
            f"Recommendations ready: top score={result['final_score'].iloc[0]:.4f}"
        )
        return result

    # ──────────────────────────────────────────────────────────
    #  SAVE / LOAD
    # ──────────────────────────────────────────────────────────

    def save(self) -> None:
        """Save both sub-models to disk."""
        self.content_model.save()
        self.ml_model.save()
        log.info("HybridRecommendationEngine saved ✓")

    def load(self) -> "HybridRecommendationEngine":
        """Load both sub-models from disk."""
        self.content_model.load()
        self.ml_model.load()
        log.info("HybridRecommendationEngine loaded ✓")
        return self

    def is_ready(self) -> bool:
        """Return True if both sub-models are available on disk."""
        return self.content_model.is_saved() and self.ml_model.is_saved()

    # ──────────────────────────────────────────────────────────
    #  PRIVATE
    # ──────────────────────────────────────────────────────────

    def _score_with_ml(
        self,
        user: pd.Series,
        candidates: pd.DataFrame,
    ) -> np.ndarray:
        """
        Build a feature dict for each candidate job and predict
        match probability using the ML classifier.

        Returns:
            numpy array of probabilities aligned with candidates.
        """
        probs = []

        for _, job in candidates.iterrows():
            # ── Reconstruct features for this (user, job) pair ──
            u_sal_min, u_sal_max = _parse_salary_range(
                user.get("expected_salary_egp", "0-0")
            )
            j_sal_min, j_sal_max = _parse_salary_range(
                job.get("salary_range_egp", "0-0")
            )

            features = {
                "skill_match_score": _skill_match(
                    user.get("user_skills", ""),
                    job.get("job_required_skills", ""),
                ),
                "location_match": int(
                    user.get("user_location", "") == job.get("job_location", "")
                ),
                "salary_fit": int(
                    j_sal_min <= u_sal_max and j_sal_max >= u_sal_min
                ),
                "experience_fit": int(
                    user.get("experience_years", 0)
                    >= _parse_exp_min(job.get("experience_required", "0"))
                ),
                "job_type_match": _job_type_match(
                    user.get("preferred_job_type", ""),
                    job.get("job_type", ""),
                ),
                # For real-time inference, interaction_score is unknown
                # → use a neutral baseline of 3 (out of 6 max)
                "interaction_score": 3,
                "experience_years" : user.get("experience_years", 0),
            }

            prob = self.ml_model.predict_proba(features)
            probs.append(prob)

        return np.array(probs)
