"""
utils/exporters.py
==================
Export DataFrames to CSV and Excel formats for download buttons.
"""

import io
import pandas as pd
from datetime import datetime


def df_to_csv(df: pd.DataFrame) -> bytes:
    """Converts a DataFrame to UTF-8 CSV bytes."""
    return df.to_csv(index=False).encode("utf-8")


def df_to_excel(df: pd.DataFrame, sheet_name: str = "Attendance") -> bytes:
    """
    Converts a DataFrame to Excel bytes using openpyxl.
    Applies basic formatting: header bold, column auto-width.
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        workbook  = writer.book
        worksheet = writer.sheets[sheet_name]

        # Auto-size columns
        for col_cells in worksheet.columns:
            max_len = max(
                (len(str(cell.value)) if cell.value else 0)
                for cell in col_cells
            )
            col_letter = col_cells[0].column_letter
            worksheet.column_dimensions[col_letter].width = min(max_len + 4, 50)

        # Bold header row
        from openpyxl.styles import Font, PatternFill, Alignment
        header_fill = PatternFill("solid", fgColor="6C63FF")
        for cell in worksheet[1]:
            cell.font      = Font(bold=True, color="FFFFFF")
            cell.fill      = header_fill
            cell.alignment = Alignment(horizontal="center")

    return buffer.getvalue()


def make_filename(prefix: str, ext: str) -> str:
    """Generates a timestamped filename."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}.{ext}"
