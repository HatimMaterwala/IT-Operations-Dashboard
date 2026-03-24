import psutil
import sqlite3
import datetime
import os

# ── Path setup ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "data", "metrics.db")

# ── Thresholds for auto incident detection ───────────────────
THRESHOLDS = {
    "cpu":    85.0,   # %
    "ram":    85.0,   # %
    "disk":   90.0,   # %
}

# ── Database setup ───────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT,
            cpu_percent REAL,
            ram_percent REAL,
            ram_used_gb REAL,
            disk_percent REAL,
            disk_used_gb REAL,
            net_sent_mb REAL,
            net_recv_mb REAL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT,
            type        TEXT,
            severity    TEXT,
            value       REAL,
            description TEXT,
            resolved    INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

# ── Collect metrics ──────────────────────────────────────────
def collect_metrics():
    cpu     = psutil.cpu_percent(interval=1)
    ram     = psutil.virtual_memory()
    disk    = psutil.disk_usage("/")
    net     = psutil.net_io_counters()

    return {
        "timestamp":    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cpu_percent":  cpu,
        "ram_percent":  ram.percent,
        "ram_used_gb":  round(ram.used / (1024**3), 2),
        "disk_percent": disk.percent,
        "disk_used_gb": round(disk.used  / (1024**3), 2),
        "net_sent_mb":  round(net.bytes_sent / (1024**2), 2),
        "net_recv_mb":  round(net.bytes_recv / (1024**2), 2),
    }

# ── Save metrics to DB ───────────────────────────────────────
def save_metrics(m):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO metrics
        (timestamp, cpu_percent, ram_percent, ram_used_gb,
         disk_percent, disk_used_gb, net_sent_mb, net_recv_mb)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        m["timestamp"], m["cpu_percent"], m["ram_percent"],
        m["ram_used_gb"], m["disk_percent"], m["disk_used_gb"],
        m["net_sent_mb"], m["net_recv_mb"]
    ))
    conn.commit()
    conn.close()

# ── Auto incident detection ──────────────────────────────────
def check_incidents(m):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    checks = [
        ("cpu",  m["cpu_percent"],  "CPU",  "High CPU Usage"),
        ("ram",  m["ram_percent"],  "RAM",  "High RAM Usage"),
        ("disk", m["disk_percent"], "DISK", "Low Disk Space"),
    ]

    for key, value, itype, desc in checks:
        if value >= THRESHOLDS[key]:
            severity = "CRITICAL" if value >= 95 else "HIGH" if value >= 90 else "MEDIUM"
            c.execute("""
                INSERT INTO incidents (timestamp, type, severity, value, description)
                VALUES (?,?,?,?,?)
            """, (m["timestamp"], itype, severity, value,
                  f"{desc}: {value}% (threshold: {THRESHOLDS[key]}%)"))
            print(f"  ⚠️  INCIDENT LOGGED → [{severity}] {desc}: {value}%")

    conn.commit()
    conn.close()

# ── Single collection run ────────────────────────────────────
def run_once():
    metrics = collect_metrics()
    save_metrics(metrics)
    check_incidents(metrics)
    print(f"[{metrics['timestamp']}] CPU: {metrics['cpu_percent']}% | "
          f"RAM: {metrics['ram_percent']}% | Disk: {metrics['disk_percent']}%")
    return metrics

if __name__ == "__main__":
    init_db()
    print("✅ Database initialized")
    print("🔍 Collecting first metrics snapshot...")
    run_once()
    print("\nDone. Check your data/metrics.db file.")