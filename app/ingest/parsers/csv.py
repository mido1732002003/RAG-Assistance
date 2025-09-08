"""CSV file parser."""

from pathlib import Path
from typing import Dict, Any
import pandas as pd

from app.ingest.parsers.base import BaseParser
from app.utils.logging import get_logger

logger = get_logger(__name__)


class CSVParser(BaseParser):
    """Parse CSV files."""
    
    async def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse CSV file."""
        if not self.validate_file(file_path):
            raise ValueError(f"Invalid file: {file_path}")
        
        try:
            # Read CSV
            df = pd.read_csv(file_path)
            
            # Convert to text representation
            text_parts = []
            
            # Add column names
            text_parts.append(f"Columns: {', '.join(df.columns)}")
            text_parts.append(f"Rows: {len(df)}")
            text_parts.append("")
            
            # Add summary statistics for numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                text_parts.append("Summary Statistics:")
                for col in numeric_cols:
                    text_parts.append(f"  {col}: mean={df[col].mean():.2f}, std={df[col].std():.2f}")
                text_parts.append("")
            
            # Add first few rows as sample
            text_parts.append("Sample Data:")
            sample_df = df.head(20)
            text_parts.append(sample_df.to_string())
            
            text = "\n".join(text_parts)
            
            return {
                "text": text,
                "metadata": {
                    "columns": list(df.columns),
                    "row_count": len(df),
                },
                "mime_type": "text/csv",
                "title": file_path.stem,
            }
            
        except Exception as e:
            logger.error(f"Failed to parse CSV {file_path}: {e}")
            raise