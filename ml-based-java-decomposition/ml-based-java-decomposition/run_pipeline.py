#!/usr/bin/env python3
"""
ML-Based Java Decomposition Pipeline

Based on Research (2023-2025):
- Rao et al. (2023): PCA + SMOTE + Random Forest (99%)
- Dewangan et al. (2023): 4-level severity + XGBoost (99.12%)
- Khleel & Nehéz (2024): Data balancing techniques

Usage:
    python run_pipeline.py --demo     # Run demo
    python run_pipeline.py --all      # Full pipeline
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

import yaml
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "src"))

from feature_extraction.metric_extractor import MetricExtractor
from models.ml_classifier import SeverityClassifier, generate_synthetic_training_data


def setup_logging(config: dict) -> logging.Logger:
    """Configure logging."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("logs/ml_analysis.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration."""
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except:
        return {
            "data": {"sample_dir": "data/sample", "processed_dir": "data/processed"},
            "output": {"results_dir": "results", "models_dir": "results/models"}
        }


def run_demo(config: dict, logger: logging.Logger):
    """Run complete demo on sample files."""
    logger.info("=" * 70)
    logger.info("ML-BASED GOD CLASS DETECTION - DEMO")
    logger.info("=" * 70)
    logger.info("\nResearch Foundation:")
    logger.info("  • Rao et al. (2023) - PCA + SMOTE + Random Forest")
    logger.info("  • Dewangan et al. (2023) - 4-level severity classification")
    logger.info("  • Khleel & Nehéz (2024) - Data balancing techniques")
    logger.info("=" * 70)
    
    sample_dir = Path(config.get("data", {}).get("sample_dir", "data/sample"))
    if not sample_dir.exists() or not list(sample_dir.glob("*.java")):
        logger.error(f"No Java files in {sample_dir}")
        return
    
    # Step 1: Extract Metrics
    logger.info("\n" + "="*70)
    logger.info("Step 1: Extracting Code Metrics")
    logger.info("="*70)
    
    extractor = MetricExtractor(config)
    metrics_list = []
    
    for java_file in sorted(sample_dir.glob("*.java")):
        metrics = extractor.extract_metrics_from_file(str(java_file))
        if metrics:
            metrics_list.append(metrics)
            logger.info(f"\n{metrics.class_name}:")
            logger.info(f"  LOC:        {metrics.loc}")
            logger.info(f"  NOM:        {metrics.nom}")
            logger.info(f"  WMC:        {metrics.wmc}")
            logger.info(f"  CBO:        {metrics.cbo}")
            logger.info(f"  LCOM:       {metrics.lcom:.4f}")
            logger.info(f"  Cyclomatic: {metrics.cyclomatic}")
    
    if not metrics_list:
        logger.error("No metrics extracted!")
        return
    
    # Step 2: Train Model
    logger.info("\n" + "="*70)
    logger.info("Step 2: Training ML Model")
    logger.info("="*70)
    
    logger.info("Generating synthetic training data (2000 samples)...")
    X_train, y_train = generate_synthetic_training_data(n_samples=2000)
    feature_names = ['loc', 'sloc', 'wmc', 'cyclomatic', 'cbo', 'lcom', 'nom', 'noa']
    
    classifier = SeverityClassifier(config)
    performances = classifier.train(X_train, y_train, feature_names)
    
    best = max(performances.items(), key=lambda x: x[1].f1_score)
    logger.info(f"\nBest model: {best[0]} (F1={best[1].f1_score:.4f})")
    
    for name, perf in performances.items():
        logger.info(f"  {name}: Acc={perf.accuracy:.4f}, F1={perf.f1_score:.4f}, "
                   f"CV={perf.cv_mean:.4f}±{perf.cv_std:.4f}")
    
    # Step 3: Classify Files
    logger.info("\n" + "="*70)
    logger.info("Step 3: Classifying Sample Files")
    logger.info("="*70)
    
    results = []
    for metrics in metrics_list:
        features = {
            'loc': metrics.loc, 'sloc': metrics.sloc, 'wmc': metrics.wmc,
            'cyclomatic': metrics.cyclomatic, 'cbo': metrics.cbo,
            'lcom': metrics.lcom, 'nom': metrics.nom, 'noa': metrics.noa,
            'class_name': metrics.class_name, 'file_path': metrics.file_path
        }
        
        result = classifier.classify_file(features)
        results.append(result)
        
        icon = "🔴" if result.predicted_severity == "CRITICAL" else \
               "🟠" if result.predicted_severity == "MAJOR" else \
               "🟡" if result.predicted_severity == "MINOR" else "🟢"
        
        logger.info(f"\n{icon} {metrics.class_name}:")
        logger.info(f"   Severity:     {result.predicted_severity}")
        logger.info(f"   Confidence:   {result.confidence:.1f}%")
        logger.info(f"   God Class:    {'YES' if result.is_god_class else 'NO'}")
        logger.info(f"   Recommendation: {result.recommendation}")
    
    # Step 4: Feature Importance
    logger.info("\n" + "="*70)
    logger.info("Step 4: Feature Importance Analysis")
    logger.info("="*70)
    
    importance = classifier.get_feature_importance('random_forest')
    for feat, imp in list(importance.items())[:8]:
        bar = '█' * int(imp * 40)
        logger.info(f"  {feat:15s}: {imp:.4f} {bar}")
    
    # Step 5: Save Results
    logger.info("\n" + "="*70)
    logger.info("Step 5: Saving Results")
    logger.info("="*70)
    
    results_dir = Path("results/demo_output")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    with open(results_dir / "demo_results.json", 'w') as f:
        json.dump([r.to_dict() for r in results], f, indent=2)
    
    classifier.save_model(str(results_dir / "demo_model.pkl"))
    logger.info(f"Results saved to: {results_dir}")
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("DEMO COMPLETE - SUMMARY")
    logger.info("="*70)
    
    counts = {}
    for r in results:
        counts[r.predicted_severity] = counts.get(r.predicted_severity, 0) + 1
    
    logger.info(f"\nFiles analyzed: {len(results)}")
    for sev in ['NONE', 'MINOR', 'MAJOR', 'CRITICAL']:
        if sev in counts:
            logger.info(f"  {sev}: {counts[sev]}")
    
    god_classes = sum(1 for r in results if r.is_god_class)
    logger.info(f"\nGod Classes detected: {god_classes}/{len(results)}")
    logger.info(f"Best model accuracy: {best[1].accuracy:.2%}")


def run_extract(config: dict, logger: logging.Logger) -> pd.DataFrame:
    """Extract metrics from Java files."""
    logger.info("=" * 70)
    logger.info("PHASE 1: METRIC EXTRACTION")
    logger.info("=" * 70)
    
    extractor = MetricExtractor(config)
    metrics_df = extractor.extract_all_metrics()
    
    if not metrics_df.empty:
        output_dir = Path(config.get("data", {}).get("processed_dir", "data/processed"))
        output_dir.mkdir(parents=True, exist_ok=True)
        metrics_df.to_csv(output_dir / "raw_metrics.csv", index=False)
        logger.info(f"Saved metrics for {len(metrics_df)} classes")
    
    return metrics_df


def run_train(config: dict, logger: logging.Logger):
    """Train ML models."""
    logger.info("=" * 70)
    logger.info("PHASE 2: MODEL TRAINING")
    logger.info("=" * 70)
    
    X, y = generate_synthetic_training_data(n_samples=2000)
    feature_names = ['loc', 'sloc', 'wmc', 'cyclomatic', 'cbo', 'lcom', 'nom', 'noa']
    
    classifier = SeverityClassifier(config)
    performances = classifier.train(X, y, feature_names)
    
    for name, perf in performances.items():
        logger.info(f"{name}: Acc={perf.accuracy:.4f}, F1={perf.f1_score:.4f}")
    
    models_dir = Path(config.get("output", {}).get("models_dir", "results/models"))
    models_dir.mkdir(parents=True, exist_ok=True)
    classifier.save_model(str(models_dir / "trained_model.pkl"))
    
    return performances


def run_predict(config: dict, logger: logging.Logger):
    """Run predictions."""
    logger.info("=" * 70)
    logger.info("PHASE 3: PREDICTION")
    logger.info("=" * 70)
    
    models_dir = Path(config.get("output", {}).get("models_dir", "results/models"))
    model_path = models_dir / "trained_model.pkl"
    
    if not model_path.exists():
        logger.error("Model not found. Run --train first.")
        return
    
    classifier = SeverityClassifier(config)
    classifier.load_model(str(model_path))
    
    processed_dir = Path(config.get("data", {}).get("processed_dir", "data/processed"))
    metrics_file = processed_dir / "raw_metrics.csv"
    
    if not metrics_file.exists():
        logger.error("Metrics not found. Run --extract first.")
        return
    
    metrics_df = pd.read_csv(metrics_file)
    results = []
    
    for _, row in metrics_df.iterrows():
        result = classifier.classify_file(row.to_dict())
        results.append(result.to_dict())
        logger.info(f"{row['class_name']}: {result.predicted_severity} ({result.confidence:.1f}%)")
    
    results_dir = Path(config.get("output", {}).get("results_dir", "results"))
    results_dir.mkdir(parents=True, exist_ok=True)
    
    with open(results_dir / "classification_results.json", 'w') as f:
        json.dump(results, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="ML-Based Java Class Decomposition")
    parser.add_argument("--demo", action="store_true", help="Run demo")
    parser.add_argument("--all", action="store_true", help="Run full pipeline")
    parser.add_argument("--extract", action="store_true", help="Extract metrics")
    parser.add_argument("--train", action="store_true", help="Train models")
    parser.add_argument("--predict", action="store_true", help="Run predictions")
    parser.add_argument("--config", default="config.yaml", help="Config file")
    
    args = parser.parse_args()
    config = load_config(args.config)
    logger = setup_logging(config)
    
    logger.info("=" * 70)
    logger.info("ML-Based Java Class Decomposition Tool v1.0")
    logger.info("Research-Based Implementation (2023-2025)")
    logger.info("=" * 70)
    
    try:
        if args.demo:
            run_demo(config, logger)
        elif args.all:
            run_extract(config, logger)
            run_train(config, logger)
            run_predict(config, logger)
        elif args.extract:
            run_extract(config, logger)
        elif args.train:
            run_train(config, logger)
        elif args.predict:
            run_predict(config, logger)
        else:
            parser.print_help()
            logger.info("\nQuick start: python run_pipeline.py --demo")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
