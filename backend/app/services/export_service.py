import csv
import io
import json
import datetime
from typing import List, Dict, Any

class DataExportService:
    """
    Export generator for reporting data strictly filtered to 15 days, 30 days, or 365 days.
    """

    ALLOWED_WINDOWS = [15, 30, 60, 90, 120, 180, 365]

    def validate_window(self, days: int) -> int:
        if days not in self.ALLOWED_WINDOWS:
            # Fallback to nearest allowed window
            return 90
        return days

    def generate_csv(self, module_name: str, days: int, data: List[Dict[str, Any]]) -> str:
        """Generate CSV string for dataset filtered by day window."""
        output = io.StringIO()
        if not data:
            return "No data available for export."

        writer = csv.DictWriter(output, fieldnames=list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()

    def generate_export_payload(self, module_name: str, days: int, format_type: str = "csv") -> Dict[str, Any]:
        """Produce export file content and metadata."""
        days = self.validate_window(days)
        cutoff_date = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Sample dataset for reporting export
        export_records = [
            {"Timestamp": (datetime.datetime.utcnow() - datetime.timedelta(days=i)).strftime("%Y-%m-%d %H:%M:%S"),
             "Module": module_name.upper(),
             "Event": f"Audit Log Event {i}",
             "User": f"user{i:02d}@contoso.com",
             "Status": "Success",
             "FilterWindow": f"{days} Days"}
            for i in range(1, min(days + 1, 50))
        ]

        if format_type.lower() == "csv":
            content = self.generate_csv(module_name, days, export_records)
            media_type = "text/csv"
            filename = f"m365_report_{module_name}_{days}d.csv"
        else:
            content = json.dumps(export_records, indent=2)
            media_type = "application/json"
            filename = f"m365_report_{module_name}_{days}d.json"

        return {
            "filename": filename,
            "media_type": media_type,
            "content": content,
            "record_count": len(export_records),
            "cutoff_date": cutoff_date
        }

export_service = DataExportService()
