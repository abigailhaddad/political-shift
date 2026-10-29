"""Shared paths, comparison months, and the definition of a political appointee."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"          # accessions
RAW_SEP = DATA / "raw_sep"  # separations
OUT = ROOT / "output"

# Employment snapshots compared: a full Biden-era appointee corps against the latest month.
BASE, END = "202410", "202608"

# Schedule C, noncareer SES, presidential/executive appointments. Anyone on the Executive Schedule
# (pay plan EX) also counts: some carry an invalid or non-political appointment code.
POLITICAL_APPT = ("44", "55", "46", "36")
POLITICAL_SQL = f"(appointment_type_code in {POLITICAL_APPT} or pay_plan_code = 'EX')"
