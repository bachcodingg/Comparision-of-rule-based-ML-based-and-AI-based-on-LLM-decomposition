#!/usr/bin/env python3
"""
Rule-Based Java Decomposition Pipeline - Updated for Research-Based Approach

Main entry point for running rule-based analysis on Java repositories
to detect classes that should be decomposed AND perform actual decomposition.

Based on Recent Research (2022-2023):
- Dewangan et al. (2023): 4-level severity classification
- Verma et al. (2023): Priority scoring approach
- Rao et al. (2023): Empirical threshold validation
- Gupta & Chauhan (2022): Java-specific severity assessment

Usage:
    python run_pipeline.py --all           # Run complete pipeline
    python run_pipeline.py --collect       # Only collect data
    python run_pipeline.py --extract       # Only extract metrics
    python run_pipeline.py --analyze       # Only run analysis
    python run_pipeline.py --prioritize    # Only calculate priorities
    python run_pipeline.py --decompose     # Only run decomposition
    python run_pipeline.py --report        # Only generate report
    python run_pipeline.py --demo          # Run demo on sample file

Updated: January 2026
Version: 2.0
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

import yaml
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from analyzer.rule_analyzer import RuleBasedAnalyzer
from analyzer.priority_scorer import SeverityBasedScorer
from metrics.metric_extractor import MetricExtractor
from utils.data_collector import DataCollector
from utils.report_generator import ReportGenerator
from decomposer.decomposer import JavaClassDecomposer, decompose_java_file


def setup_logging(config: dict) -> logging.Logger:
    """Configure logging based on config settings."""
    log_config = config.get("logging", {})
    
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_config.get("level", "INFO")),
        format=log_config.get("format", "%(asctime)s - %(levelname)s - %(message)s"),
        handlers=[
            logging.FileHandler(log_config.get("file", "logs/analysis.log")),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def run_data_collection(config: dict, logger: logging.Logger) -> None:
    """Collect and clone repositories for analysis."""
    logger.info("=" * 60)
    logger.info("PHASE 1: DATA COLLECTION")
    logger.info("=" * 60)
    
    collector = DataCollector(config)
    
    # Clone repositories
    logger.info("Cloning repositories...")
    collector.clone_repositories()
    
    logger.info("Data collection complete!")


def run_metric_extraction(config: dict, logger: logging.Logger) -> pd.DataFrame:
    """Extract metrics from Java files."""
    logger.info("=" * 60)
    logger.info("PHASE 2: METRIC EXTRACTION")
    logger.info("=" * 60)
    
    # Extract metrics from Java files
    logger.info("Extracting code metrics...")
    extractor = MetricExtractor(config)
    metrics_df = extractor.extract_all_metrics()
    
    # Save metrics
    output_path = Path(config["data"]["processed_dir"]) / "code_metrics.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_df.to_csv(output_path, index=False)
    logger.info(f"Saved metrics for {len(metrics_df)} classes to {output_path}")
    
    return metrics_df


def run_analysis(config: dict, logger: logging.Logger) -> pd.DataFrame:
    """Run rule-based analysis with 4-level severity system."""
    logger.info("=" * 60)
    logger.info("PHASE 3: RULE-BASED ANALYSIS")
    logger.info("=" * 60)
    
    analyzer = RuleBasedAnalyzer(config)
    results_df = analyzer.run_full_analysis()
    
    logger.info(f"Analysis complete!")
    logger.info(f"Total classes analyzed: {len(results_df)}")
    logger.info(f"God Class candidates: {results_df['is_god_class_candidate'].sum()}")
    
    # Show severity distribution
    logger.info("\nViolation Summary:")
    logger.info(f"  LOW violations: {results_df['low_violations'].sum()}")
    logger.info(f"  MEDIUM violations: {results_df['medium_violations'].sum()}")
    logger.info(f"  HIGH violations: {results_df['high_violations'].sum()}")
    logger.info(f"  CRITICAL violations: {results_df['critical_violations'].sum()}")
    
    return results_df


def run_prioritization(config: dict, logger: logging.Logger) -> pd.DataFrame:
    """Calculate priority scores using severity-based approach."""
    logger.info("=" * 60)
    logger.info("PHASE 4: PRIORITY CALCULATION")
    logger.info("=" * 60)
    
    # Load metrics
    metrics_file = Path(config["data"]["processed_dir"]) / "code_metrics.csv"
    if not metrics_file.exists():
        logger.error(f"Metrics file not found: {metrics_file}")
        logger.error("Please run metric extraction first: python run_pipeline.py --extract")
        return pd.DataFrame()
    
    metrics_df = pd.read_csv(metrics_file)
    
    # Calculate priorities using severity-based scorer
    logger.info("Calculating priority scores...")
    scorer = SeverityBasedScorer()
    ranked_df = scorer.rank_classes(metrics_df)
    
    # Save results
    output_path = Path(config["output"]["results_dir"]) / "priority_rankings.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ranked_df.to_csv(output_path, index=False)
    
    logger.info(f"Priority calculation complete!")
    logger.info(f"Total classes ranked: {len(ranked_df)}")
    
    # Show priority distribution
    logger.info("\nPriority Distribution:")
    logger.info(f"  LOW: {(ranked_df['priority_label'] == 'LOW').sum()}")
    logger.info(f"  MEDIUM: {(ranked_df['priority_label'] == 'MEDIUM').sum()}")
    logger.info(f"  HIGH: {(ranked_df['priority_label'] == 'HIGH').sum()}")
    logger.info(f"  CRITICAL: {(ranked_df['priority_label'] == 'CRITICAL').sum()}")
    
    # Show top 10
    logger.info("\nTop 10 Priority Classes:")
    for idx, row in ranked_df.head(10).iterrows():
        logger.info(f"  {row['rank']}. {row['class_name']}: {row['priority_score']:.2f} ({row['priority_label']})")
    
    return ranked_df


def run_decomposition(config: dict, logger: logging.Logger) -> None:
    """Run decomposition on flagged classes."""
    logger.info("=" * 60)
    logger.info("PHASE 5: CLASS DECOMPOSITION")
    logger.info("=" * 60)
    
    # Load analysis results
    results_file = Path(config["output"]["results_dir"]) / "analysis_results.csv"
    if not results_file.exists():
        logger.error(f"Analysis results not found: {results_file}")
        logger.error("Please run analysis first: python run_pipeline.py --analyze")
        return
    
    results_df = pd.read_csv(results_file)
    
    # Get God Class candidates
    candidates = results_df[results_df['is_god_class_candidate'] == True]
    logger.info(f"Found {len(candidates)} God Class candidates for decomposition")
    
    if len(candidates) == 0:
        logger.info("No classes need decomposition!")
        return
    
    # Decompose each candidate
    decomposer = JavaClassDecomposer(config)
    decomposed_count = 0
    
    for _, row in candidates.head(10).iterrows():  # Limit to top 10
        class_name = row['class_name']
        file_path = row['file_path']
        
        logger.info(f"Decomposing: {class_name}")
        
        try:
            suggestions = decompose_java_file(file_path, config)
            if suggestions:
                decomposed_count += 1
                logger.info(f"  -> Suggested {len(suggestions)} extracted classes")
        except Exception as e:
            logger.error(f"  -> Error: {e}")
    
    logger.info(f"Decomposition complete! Processed {decomposed_count} classes")


def run_report_generation(config: dict, logger: logging.Logger) -> None:
    """Generate HTML report."""
    logger.info("=" * 60)
    logger.info("PHASE 6: REPORT GENERATION")
    logger.info("=" * 60)
    
    # Load results data
    results_dir = Path(config["output"]["results_dir"])
    metrics_file = Path(config["data"]["processed_dir"]) / "code_metrics.csv"
    analysis_file = results_dir / "analysis_results.csv"
    priority_file = results_dir / "priority_rankings.csv"
    
    # Check if required files exist
    if not metrics_file.exists():
        logger.error(f"Metrics file not found: {metrics_file}")
        logger.error("Please run --extract first")
        return
    
    # Load metrics
    metrics_df = pd.read_csv(metrics_file)
    
    # Load analysis results if available
    if analysis_file.exists():
        analysis_df = pd.read_csv(analysis_file)
    else:
        analysis_df = pd.DataFrame()
        logger.warning("Analysis results not found, generating partial report")
    
    # Load priority rankings if available  
    if priority_file.exists():
        priority_df = pd.read_csv(priority_file)
    else:
        priority_df = pd.DataFrame()
        logger.warning("Priority rankings not found, generating partial report")
    
    # Prepare results dictionary
    results = {
        "final": priority_df if not priority_df.empty else analysis_df,
        "analysis": analysis_df,
        "priority": priority_df
    }
    
    # Prepare metrics dictionary
    metrics = {
        "total_classes": len(metrics_df),
        "metrics_df": metrics_df
    }
    
    generator = ReportGenerator(config)
    report_path = generator.generate_html_report(results, metrics)
    
    logger.info(f"Report generated: {report_path}")
    logger.info("Open this file in your browser to view results")


def run_demo(config: dict, logger: logging.Logger) -> None:
    """Run demo analysis on sample file."""
    logger.info("=" * 70)
    logger.info("DEMO MODE: Analyzing Sample File")
    logger.info("=" * 70)
    
    # Check for sample file
    sample_file = Path("data/sample/UserService.java")
    if not sample_file.exists():
        logger.error(f"Sample file not found: {sample_file}")
        logger.error("Please create a sample Java file in data/sample/")
        return
    
    logger.info(f"Loading sample file: {sample_file}")
    
    # Extract metrics
    logger.info("\n" + "="*70)
    logger.info("Step 1: Extracting Metrics")
    logger.info("="*70)
    
    extractor = MetricExtractor(config)
    metrics = extractor.extract_metrics_from_file(sample_file)
    
    logger.info(f"\nMetrics for {sample_file.name}:")
    logger.info(f"  LOC (Lines of Code): {metrics['loc']}")
    logger.info(f"  NOM (Number of Methods): {metrics['nom']}")
    logger.info(f"  WMC (Weighted Methods per Class): {metrics['wmc']}")
    logger.info(f"  CBO (Coupling Between Objects): {metrics['cbo']}")
    logger.info(f"  LCOM (Lack of Cohesion): {metrics['lcom']:.2f}")
    
    # Calculate priority
    logger.info("\n" + "="*70)
    logger.info("Step 2: Calculating Priority Score")
    logger.info("="*70)
    
    scorer = SeverityBasedScorer()
    score, details = scorer.calculate_priority(metrics)
    
    logger.info(f"\nPriority Score: {score:.2f} / 4.00")
    logger.info(f"Priority Label: {details['priority_label']}")
    logger.info(f"God Class Candidate: {'Yes' if details['is_god_class_candidate'] else 'No'}")
    logger.info(f"Recommendation: {details['recommendation']}")
    
    # Show severity breakdown
    logger.info("\n" + "="*70)
    logger.info("Step 3: Severity Analysis")
    logger.info("="*70)
    
    logger.info("\nMetric Severity Levels:")
    for metric, contrib in details['contributions'].items():
        logger.info(f"  {metric.upper():5s}: {contrib['value']:6.1f} -> "
                   f"{contrib['severity']:8s} (score={contrib['severity_score']}) x "
                   f"weight={contrib['weight']:.2f} = {contrib['contribution']:.2f}")
    
    logger.info("\nSeverity Distribution:")
    for level, count in details['severity_counts'].items():
        logger.info(f"  {level.capitalize():8s}: {count} metrics")
    
    # Detection rule check
    logger.info("\n" + "="*70)
    logger.info("Step 4: God Class Detection Rule")
    logger.info("="*70)
    
    high_critical = details['severity_counts']['high'] + details['severity_counts']['critical']
    logger.info(f"\nDetection Rule: 2+ metrics at HIGH or CRITICAL level")
    logger.info(f"Your class: {high_critical} metrics at HIGH/CRITICAL")
    logger.info(f"Result: {'FLAGGED' if details['is_god_class_candidate'] else 'NOT FLAGGED'}")
    
    # Decomposition suggestions
    if details['is_god_class_candidate']:
        logger.info("\n" + "="*70)
        logger.info("Step 5: Decomposition Suggestions")
        logger.info("="*70)
        
        logger.info("\nRecommended Actions:")
        logger.info(f"  1. Extract related methods into helper classes")
        logger.info(f"  2. Focus on methods with high coupling")
        logger.info(f"  3. Separate concerns based on cohesion")
        logger.info(f"  4. Target: Reduce LOC to <300, NOM to <20")
    
    # Save demo results
    logger.info("\n" + "="*70)
    logger.info("Step 6: Saving Results")
    logger.info("="*70)
    
    demo_output_dir = Path("results/demo_output")
    demo_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save metrics
    metrics_output = demo_output_dir / "demo_metrics.json"
    with open(metrics_output, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved metrics to: {metrics_output}")
    
    # Save priority details
    priority_output = demo_output_dir / "demo_priority.json"
    # Convert details to JSON-serializable format
    json_details = {
        'priority_score': details['priority_score'],
        'priority_label': details['priority_label'],
        'recommendation': details['recommendation'],
        'is_god_class_candidate': details['is_god_class_candidate'],
        'severity_counts': details['severity_counts'],
        'weights': details['weights']
    }
    with open(priority_output, 'w') as f:
        json.dump(json_details, f, indent=2)
    logger.info(f"Saved priority analysis to: {priority_output}")
    
    logger.info("\n" + "="*70)
    logger.info("DEMO COMPLETE!")
    logger.info("="*70)
    logger.info(f"\nResults saved to: {demo_output_dir}")
    logger.info(f"Priority: {score:.2f} ({details['priority_label']})")
    logger.info(f"Status: {'NEEDS REFACTORING' if details['is_god_class_candidate'] else 'OK'}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Rule-Based Java Class Decomposition Tool (Research-Based v2.0)"
    )
    
    parser.add_argument("--all", action="store_true",
                       help="Run complete pipeline (collect, extract, analyze, prioritize, report)")
    parser.add_argument("--collect", action="store_true",
                       help="Phase 1: Collect and clone repositories")
    parser.add_argument("--extract", action="store_true",
                       help="Phase 2: Extract metrics from Java files")
    parser.add_argument("--analyze", action="store_true",
                       help="Phase 3: Run rule-based analysis")
    parser.add_argument("--prioritize", action="store_true",
                       help="Phase 4: Calculate priority scores")
    parser.add_argument("--decompose", action="store_true",
                       help="Phase 5: Run decomposition on flagged classes")
    parser.add_argument("--report", action="store_true",
                       help="Phase 6: Generate HTML report")
    parser.add_argument("--demo", action="store_true",
                       help="Run demo on sample file")
    parser.add_argument("--config", default="config.yaml",
                       help="Path to config file (default: config.yaml)")
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"Error: Config file not found: {args.config}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing config file: {e}")
        sys.exit(1)
    
    # Setup logging
    logger = setup_logging(config)
    
    logger.info("=" * 70)
    logger.info("Rule-Based Java Class Decomposition Tool")
    logger.info("Version 2.0 - Research-Based Approach (2022-2023)")
    logger.info("=" * 70)
    logger.info(f"Research Foundation:")
    logger.info(f"  * Dewangan et al. (2023) - 4-level severity classification")
    logger.info(f"  * Verma et al. (2023) - Priority scoring approach")
    logger.info(f"  * Rao et al. (2023) - Empirical threshold validation")
    logger.info(f"  * Gupta & Chauhan (2022) - Java-specific assessment")
    logger.info("=" * 70)
    
    try:
        # Demo mode
        if args.demo:
            run_demo(config, logger)
            return
        
        # Run all phases
        if args.all:
            run_data_collection(config, logger)
            run_metric_extraction(config, logger)
            run_analysis(config, logger)
            run_prioritization(config, logger)
            run_report_generation(config, logger)
            logger.info("\n" + "=" * 70)
            logger.info("ALL PHASES COMPLETE!")
            logger.info("=" * 70)
            return
        
        # Run individual phases
        if args.collect:
            run_data_collection(config, logger)
        
        if args.extract:
            run_metric_extraction(config, logger)
        
        if args.analyze:
            run_analysis(config, logger)
        
        if args.prioritize:
            run_prioritization(config, logger)
        
        if args.decompose:
            run_decomposition(config, logger)
        
        if args.report:
            run_report_generation(config, logger)
        
        # If no arguments, show help
        if not any([args.all, args.collect, args.extract, args.analyze, 
                   args.prioritize, args.decompose, args.report, args.demo]):
            parser.print_help()
            logger.info("\nNo action specified. Use --help for options.")
    
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\nError: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()