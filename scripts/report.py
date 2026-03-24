import sqlite3
import pandas as pd
import os
import datetime

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH     = os.path.join(BASE_DIR, "data",    "metrics.db")
REPORT_DIR  = os.path.join(BASE_DIR, "reports")

def generate_report():
    conn = sqlite3.connect(DB_PATH)

    # ── Pull data ────────────────────────────────────────────
    metrics   = pd.read_sql_query("SELECT * FROM metrics   ORDER BY timestamp DESC", conn)
    incidents = pd.read_sql_query("SELECT * FROM incidents ORDER BY timestamp DESC", conn)
    conn.close()

    if metrics.empty:
        print("No data yet — run the monitor first.")
        return

    # ── Summary stats ────────────────────────────────────────
    summary = pd.DataFrame({
        "Metric":  ["Avg CPU %", "Max CPU %", "Avg RAM %",
                    "Max RAM %", "Avg Disk %", "Total Incidents"],
        "Value": [
            round(metrics["cpu_percent"].mean(),  2),
            round(metrics["cpu_percent"].max(),   2),
            round(metrics["ram_percent"].mean(),  2),
            round(metrics["ram_percent"].max(),   2),
            round(metrics["disk_percent"].mean(), 2),
            len(incidents),
        ]
    })

    # ── Incident breakdown ───────────────────────────────────
    if not incidents.empty:
        incident_summary = incidents.groupby(["type", "severity"]).size().reset_index(name="Count")
    else:
        incident_summary = pd.DataFrame(columns=["type", "severity", "Count"])

    # ── Export to Excel ──────────────────────────────────────
    timestamp   = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    report_path = os.path.join(REPORT_DIR, f"IT_Report_{timestamp}.xlsx")

    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        metrics.to_excel(writer,          sheet_name="Raw Metrics",       index=False)
        incidents.to_excel(writer,        sheet_name="Incidents",         index=False)
        summary.to_excel(writer,          sheet_name="Summary",           index=False)
        incident_summary.to_excel(writer, sheet_name="Incident Breakdown",index=False)

    print(f"✅ Report saved → {report_path}")
    return report_path

if __name__ == "__main__":
    generate_report()