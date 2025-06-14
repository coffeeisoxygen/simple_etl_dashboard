"""Flexible CSV processor untuk ETL Dashboard."""

from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger


def find_header_row(file_path: str, header_signature: list[str]) -> int:
    """Find baris yang mengandung headers berdasarkan signature."""
    with open(file_path, encoding="utf-8") as f:
        for row_idx, line in enumerate(f):
            # Check jika line mengandung semua signature
            if all(sig in line for sig in header_signature):
                logger.debug(
                    f"Header ditemukan di baris {row_idx} di {Path(file_path).name}"
                )
                return row_idx

    raise ValueError(
        f"Header dengan signature {header_signature} tidak ditemukan di {file_path}"
    )


def process_csv_file(file_path: str, config: dict[str, Any]) -> pd.DataFrame:
    """Process single CSV file dengan config yang flexible."""
    try:
        # Get header signature dari config
        header_signature = config.get("header_signature", ["DateTime", "Transaction"])

        # Find header position
        header_row = find_header_row(file_path, header_signature)

        # Read CSV from header position
        df = pd.read_csv(file_path, skiprows=header_row)

        # Validate expected headers jika ada
        expected_headers = config.get("expected_headers", [])
        if expected_headers:
            missing_cols = set(expected_headers) - set(df.columns)
            if missing_cols:
                logger.warning(
                    f"Missing columns in {Path(file_path).name}: {list(missing_cols)[:5]}..."
                )

        logger.info(
            f"Processed {Path(file_path).name}: {len(df)} rows, {len(df.columns)} columns"
        )
        return df

    except Exception as e:
        logger.error(f"Error processing {file_path}: {str(e)}")
        raise


def load_sample_files(sample_dir: str, pattern: str = "*.csv") -> list[str]:
    """Load semua CSV files dari sample directory."""
    sample_path = Path(sample_dir)

    if not sample_path.exists():
        logger.warning(f"Sample directory tidak ditemukan: {sample_path}")
        return []

    # Find all CSV files
    csv_files = list(sample_path.glob(pattern))
    file_paths = [str(f) for f in csv_files]

    logger.info(f"Ditemukan {len(file_paths)} CSV files di {sample_path}")
    return file_paths


def combine_daily_files(file_paths: list[str], config: dict[str, Any]) -> pd.DataFrame:
    """Combine multiple daily CSV files."""
    if not file_paths:
        raise ValueError("Tidak ada file untuk diproses")

    dataframes = []

    for file_path in file_paths:
        try:
            df = process_csv_file(file_path, config)
            dataframes.append(df)
        except Exception as e:
            logger.error(f"Skip file {Path(file_path).name}: {str(e)}")
            continue

    if not dataframes:
        raise ValueError("Tidak ada file yang berhasil diproses")

    combined_df = pd.concat(dataframes, ignore_index=True)
    logger.info(f"Combined {len(dataframes)} files: {len(combined_df)} total rows")

    return combined_df
