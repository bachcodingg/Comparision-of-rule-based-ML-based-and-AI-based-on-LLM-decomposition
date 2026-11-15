#!/usr/bin/env python3
"""Metric extraction for the ML pipeline.

Values come from common/java_metrics.py (javalang syntax tree), the same code
the rule-based pipeline uses, so both pipelines see identical numbers.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from common.java_metrics import ClassMetrics, extract_metrics  # noqa: E402

JavaMetrics = ClassMetrics  # kept for callers that import the old name


class MetricExtractor:
    """Extract software metrics from Java files."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

    def extract_metrics_from_file(self, file_path: str) -> Optional[ClassMetrics]:
        try:
            return extract_metrics(file_path)
        except Exception as e:  # unparsable file: report and skip
            self.logger.error(f"Cannot extract metrics from {file_path}: {type(e).__name__}: {e}")
            return None

    def extract_all_metrics(self, directory: str = None) -> pd.DataFrame:
        if directory is None:
            directory = self.config.get('data', {}).get('sample_dir', 'data/sample')
        directory = Path(directory)
        if not directory.exists():
            self.logger.error(f"Directory not found: {directory}")
            return pd.DataFrame()
        rows = []
        for java_file in sorted(directory.glob('**/*.java')):
            metrics = self.extract_metrics_from_file(str(java_file))
            if metrics:
                rows.append(metrics.to_dict())
        return pd.DataFrame(rows)
