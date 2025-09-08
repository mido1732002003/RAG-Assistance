"""Evaluation reporting."""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def generate_report(results: Dict[str, float], output_path: Path = None) -> str:
    """Generate evaluation report."""
    report = []
    report.append("=" * 50)
    report.append("RAG EVALUATION REPORT")
    report.append(f"Generated: {datetime.now().isoformat()}")
    report.append("=" * 50)
    report.append("")
    
    report.append("RETRIEVAL METRICS:")
    report.append("-" * 20)
    for metric, value in results.items():
        report.append(f"  {metric:20s}: {value:.3f}")
    
    report_text = "\n".join(report)
    
    if output_path:
        output_path.write_text(report_text)
    
    return report_text


def save_json_report(results: Dict[str, Any], output_path: Path):
    """Save results as JSON."""
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "metrics": results
    }
    
    with open(output_path, "w") as f:
        json.dump(report_data, f, indent=2)