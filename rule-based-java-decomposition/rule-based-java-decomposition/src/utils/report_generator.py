#!/usr/bin/env python3
"""
Report Generator Module

Generates analysis reports in HTML and other formats.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates analysis reports and visualizations."""
    
    def __init__(self, config: dict):
        self.config = config
        self.results_dir = Path(config["output"]["results_dir"])
        self.reports_dir = Path(config["output"]["reports_dir"])
        self.charts_dir = Path(config["output"]["charts_dir"])
        
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.charts_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_html_report(self, results: Dict, metrics: Dict) -> Path:
        """Generate comprehensive HTML report."""
        final_df = results.get("final", pd.DataFrame())
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate summary stats safely
        total_classes = len(final_df)
        
        # Count god class candidates
        god_class_count = 0
        if total_classes > 0 and "is_god_class_candidate" in final_df.columns:
            god_class_count = int((final_df["is_god_class_candidate"] == True).sum())
        
        # Count priority levels
        critical_count = 0
        high_count = 0
        medium_count = 0
        if total_classes > 0 and "priority_label" in final_df.columns:
            critical_count = int((final_df["priority_label"] == "CRITICAL").sum())
            high_count = int((final_df["priority_label"] == "HIGH").sum())
            medium_count = int((final_df["priority_label"] == "MEDIUM").sum())
        
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rule-Based Java Decomposition Analysis Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .summary-box {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #2980b9;
        }}
        .metric-label {{
            color: #7f8c8d;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .severity-warning {{
            background-color: #fff3cd;
        }}
        .severity-critical {{
            background-color: #f8d7da;
        }}
        .severity-severe {{
            background-color: #f5c6cb;
        }}
        .footer {{
            margin-top: 40px;
            text-align: center;
            color: #7f8c8d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Rule-Based Java Decomposition Analysis Report</h1>
        <p>Generated: {timestamp}</p>
        
        <h2>Summary</h2>
        <div class="summary-box">
            <div class="metric-card">
                <div class="metric-value">{total_classes}</div>
                <div class="metric-label">Classes Analyzed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{god_class_count}</div>
                <div class="metric-label">God Class Candidates</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{critical_count}</div>
                <div class="metric-label">Critical Priority</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{high_count}</div>
                <div class="metric-label">High Priority</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{medium_count}</div>
                <div class="metric-label">Medium Priority</div>
            </div>
        </div>
        
        <h2>Top Priority Classes for Decomposition</h2>
        {self._generate_results_table(final_df.head(20))}
        
        <h2>Analysis by Repository</h2>
        {self._generate_repo_summary(final_df)}
        
        <div class="footer">
            <p>Rule-Based Java Decomposition Analysis Tool</p>
            <p>Report generated automatically</p>
        </div>
    </div>
</body>
</html>'''
        
        report_path = self.reports_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        report_path.write_text(html_content)
        
        return report_path
    
    def _generate_results_table(self, df: pd.DataFrame) -> str:
        """Generate HTML table for results."""
        if len(df) == 0:
            return "<p>No classes flagged for decomposition.</p>"
        
        rows = []
        for _, row in df.iterrows():
            # Get values with safe defaults
            rank = row.get("rank", row.get("priority_rank", "-"))
            class_name = row.get("class_name", "-")
            repo = row.get("repository", row.get("repo_name", "-"))
            score = row.get("priority_score", row.get("total_score", 0))
            label = row.get("priority_label", "-")
            is_god_class = "Yes" if row.get("is_god_class_candidate", False) else "No"
            
            # Format score safely
            try:
                score_str = f"{float(score):.2f}"
            except (ValueError, TypeError):
                score_str = str(score)
            
            # Determine row class based on priority
            row_class = ""
            if label == "CRITICAL":
                row_class = 'class="severity-critical"'
            elif label == "HIGH":
                row_class = 'class="severity-warning"'
            
            rows.append(f'''
            <tr {row_class}>
                <td>{rank}</td>
                <td>{class_name}</td>
                <td>{repo}</td>
                <td>{score_str}</td>
                <td>{label}</td>
                <td>{is_god_class}</td>
            </tr>''')
        
        return f'''
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Class Name</th>
                    <th>Repository</th>
                    <th>Priority Score</th>
                    <th>Priority Level</th>
                    <th>God Class?</th>
                </tr>
            </thead>
            <tbody>
                {"".join(rows)}
            </tbody>
        </table>'''
    
    def _generate_repo_summary(self, df: pd.DataFrame) -> str:
        """Generate repository summary."""
        if len(df) == 0:
            return "<p>No data available.</p>"
        
        # Determine which columns are available
        repo_col = "repository" if "repository" in df.columns else "repo_name" if "repo_name" in df.columns else None
        score_col = "priority_score" if "priority_score" in df.columns else "total_score" if "total_score" in df.columns else None
        
        if repo_col is None:
            return "<p>No repository information available.</p>"
        
        rows = []
        try:
            if score_col:
                summary = df.groupby(repo_col).agg({
                    "class_name": "count",
                    score_col: "mean"
                }).reset_index()
                
                for _, row in summary.iterrows():
                    rows.append(f'''
                <tr>
                    <td>{row[repo_col]}</td>
                    <td>{row["class_name"]}</td>
                    <td>{row[score_col]:.2f}</td>
                </tr>''')
            else:
                summary = df.groupby(repo_col).size().reset_index(name='count')
                
                for _, row in summary.iterrows():
                    rows.append(f'''
                <tr>
                    <td>{row[repo_col]}</td>
                    <td>{row["count"]}</td>
                    <td>N/A</td>
                </tr>''')
        except Exception as e:
            return f"<p>Error generating repository summary: {str(e)}</p>"
        
        return f'''
        <table>
            <thead>
                <tr>
                    <th>Repository</th>
                    <th>Classes Flagged</th>
                    <th>Total Score</th>
                </tr>
            </thead>
            <tbody>
                {"".join(rows)}
            </tbody>
        </table>'''
    
    def _generate_rule_summary(self, df: pd.DataFrame) -> str:
        """Generate rule violations summary."""
        if len(df) == 0:
            return "<p>No violations found.</p>"
        
        rules = {}
        for _, row in df.iterrows():
            for rule in str(row.get("rules_triggered", "")).split(", "):
                if rule:
                    rules[rule] = rules.get(rule, 0) + 1
        
        rows = []
        for rule, count in sorted(rules.items(), key=lambda x: -x[1]):
            rows.append(f'''
            <tr>
                <td>{rule}</td>
                <td>{count}</td>
            </tr>''')
        
        return f'''
        <table>
            <thead>
                <tr>
                    <th>Rule</th>
                    <th>Violations</th>
                </tr>
            </thead>
            <tbody>
                {"".join(rows)}
            </tbody>
        </table>'''
    
    def generate_charts(self, results: Dict) -> None:
        """Generate visualization charts."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            final_df = results.get("final", pd.DataFrame())
            
            if len(final_df) == 0:
                return
            
            # Violations by repository
            fig, ax = plt.subplots(figsize=(10, 6))
            repo_counts = final_df.groupby("repository").size()
            repo_counts.plot(kind="bar", ax=ax, color="#3498db")
            ax.set_title("Flagged Classes by Repository")
            ax.set_xlabel("Repository")
            ax.set_ylabel("Number of Classes")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            plt.savefig(self.charts_dir / "violations_by_repo.png", dpi=150)
            plt.close()
            
            # Score distribution
            fig, ax = plt.subplots(figsize=(10, 6))
            final_df["total_score"].hist(bins=20, ax=ax, color="#2ecc71", edgecolor="black")
            ax.set_title("Distribution of Priority Scores")
            ax.set_xlabel("Priority Score")
            ax.set_ylabel("Frequency")
            plt.tight_layout()
            plt.savefig(self.charts_dir / "score_distribution.png", dpi=150)
            plt.close()
            
            logger.info("Generated visualization charts")
            
        except ImportError:
            logger.warning("matplotlib not available. Skipping chart generation.")
    
    def generate_summary(self, results: Dict) -> Path:
        """Generate JSON summary of results."""
        final_df = results.get("final", pd.DataFrame())
        
        summary = {
            "generated_at": datetime.now().isoformat(),
            "total_classes_flagged": len(final_df),
            "classes_by_repository": final_df.groupby("repository").size().to_dict() if len(final_df) > 0 else {},
            "top_10_priority": final_df.head(10)[["class_name", "repository", "total_score"]].to_dict("records") if len(final_df) > 0 else []
        }
        
        summary_path = self.results_dir / "analysis_summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        
        return summary_path
