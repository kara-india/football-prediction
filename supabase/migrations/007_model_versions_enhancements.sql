-- Migration 007: Model Versions Enhancements
-- Adds parameter storage, evaluation metrics, and git provenance tracking to model_versions

ALTER TABLE model_versions
    ADD COLUMN IF NOT EXISTS parameters JSONB,
    ADD COLUMN IF NOT EXISTS metrics JSONB,
    ADD COLUMN IF NOT EXISTS git_sha TEXT;

COMMENT ON COLUMN model_versions.parameters IS 'Serialized parameter dictionary (alpha, beta, gamma, rho, etc.)';
COMMENT ON COLUMN model_versions.metrics IS 'Evaluation metrics (Brier score, ECE, log-loss, calibration bins)';
COMMENT ON COLUMN model_versions.git_sha IS 'Git commit SHA active when model was trained and registered';
