# FINDINGS EXPORT: write verified Part 2 numbers to narrator/findings.json
import os
import json

findings = {
    "cleaned_total_revenue_inr": float(round(cleaned_total, 2)),
    "raw_total_revenue_inr": float(round(raw_total, 2)),
    "duplicate_reconciliation_delta_inr": float(round(delta, 2)),
    "return_rate_by_payment": {
        "COD":  float(rate_by_pay["COD"]),
        "CARD": float(rate_by_pay["CARD"]),
        "UPI":  float(rate_by_pay["UPI"]),
    },
    "highest_risk_segment": {
        "payment_method": str(top_seg[0]),
        "city_tier": int(top_seg[1]),
        "return_rate_pct": float(top_seg_rate),
    },
    "true_peak_month": {
        "month": str(true_peak),
        "revenue_inr": float(monthly_corrected[true_peak]),
    },
    "outlier_inflated_month": {
        "month": str(apparent_peak),
        "apparent_revenue_inr": float(monthly_all[apparent_peak]),
        "corrected_revenue_inr": float(monthly_corrected[apparent_peak]),
    },
}

# Create the output folder if it does not exist
os.makedirs("narrator", exist_ok=True)

with open("narrator/findings.json", "w") as f:
    json.dump(findings, f, indent=2)

# print(json.dumps(findings, indent=2))

# SETUP: imports and helpers (must run BEFORE Tasks 2-5)
import os
import sys
import json
import calendar
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent if "__file__" in globals() else Path("narrator")
FINDINGS_PATH = BASE_DIR / "findings.json"

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")


def load_findings(path=FINDINGS_PATH):
    # Read the verified numbers exported by Part 2
    with open(path) as f:
        return json.load(f)


def inr(x):
    # 97358.3 -> "97,358.30"
    return f"{x:,.2f}"


def month_label(ym):
    # "2026-03" -> "March 2026"
    d = datetime.strptime(ym, "%Y-%m")
    return f"{calendar.month_name[d.month]} {d.year}"


def get_api_key():
    # 1) Environment variable (local / terminal)
    key = os.environ.get("SY_API_KEY")
    if key:
        return key
    # 2) Colab Secrets
    try:
        from google.colab import userdata
        return userdata.get("SY_API_KEY")
    except Exception:
        return None

# TASK 2a: System instruction (kept separate from the user prompt)
SYSTEM_INSTRUCTION = """You are a senior data analyst writing for Mamaearth's regional ops and finance heads.
Write a business narrative in the SCR structure with exactly three labeled sections:
Situation, Complication, Resolution.

Strict constraints:
- Every number in your output MUST come from the findings supplied by the user
  and must appear with exactly the same value.
- Do NOT invent, estimate, round differently, or calculate any new statistic.
- Use plain business language, quote currency as INR, and keep the whole narrative to about 250 words.
"""


# TASK 2b: User prompt built from the findings dict (nothing hardcoded)
def build_user_prompt(findings: dict) -> str:
    rates = ", ".join(f"{k} {v}%" for k, v in findings["return_rate_by_payment"].items())
    seg = findings["highest_risk_segment"]
    peak = findings["true_peak_month"]
    infl = findings["outlier_inflated_month"]

    return f"""Write the SCR narrative using ONLY these verified findings:

- Cleaned total revenue: INR {inr(findings['cleaned_total_revenue_inr'])}
- Raw total revenue (before cleaning): INR {inr(findings['raw_total_revenue_inr'])}
- Difference caused by removing duplicate (double-submit) orders: INR {inr(findings['duplicate_reconciliation_delta_inr'])}
- Return rate by payment method: {rates}
- Highest-risk segment: {seg['payment_method']} orders in Tier-{seg['city_tier']} cities at {seg['return_rate_pct']}% return rate
- True peak revenue month (outlier-corrected): {month_label(peak['month'])} at INR {inr(peak['revenue_inr'])}
- {month_label(infl['month'])} looked like the peak at INR {inr(infl['apparent_revenue_inr'])} but two bulk orders inflated it; corrected revenue is INR {inr(infl['corrected_revenue_inr'])}

Situation: state the cleaned revenue and the reconciliation to the raw figure.
Complication: explain where returns are concentrated and the January distortion.
Resolution: give clear actions for ops and finance, naming the true peak month.
"""

from ast import Mod
# TASK 3: Online path with locked parameters, timeout, and structured return in both branches


def generate_scr_narrative(findings: dict, api_key: str) -> dict:
    api_key = api_key or get_api_key()
    try:
        if not api_key:
            raise ValueError("No Gemini API key configured")

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        # TASK 2c: the generate_content call
        response = client.models.generate_content(
            model=MODEL,
            contents=build_user_prompt(findings),          # user prompt, built from findings
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,     # role + structure + number constraint
                # temperature=0.0: this is a factual business report, not creative writing,
                # so we want deterministic, repeatable wording with no random variation.
                temperature=0.0,
                # Explicit cap (>= 300). 1500 leaves headroom for a ~250-word 3-section narrative
                # (Gemini 2.5 models also count internal "thinking" tokens toward this limit).
                max_output_tokens=1500,
                # Request timeout in MILLISECONDS (30 s, above the 10 s minimum)
                http_options=types.HttpOptions(timeout=30_000),
            ),
        )

        text = response.text
        if not text:
            raise ValueError("Gemini returned an empty response")

        return {
            "status": "success",
            "narrative":response.text,
            "tokens": response.usage_metadata.total_token_count,
        }

    except Exception as err:
        # The caller never receives a raw exception
        return {"status": "error", "narrative": None, "message": str(err)}

generate_scr_narrative(findings, get_api_key())

# TASK 4a: Fully deterministic fallback. No network, no API key, same return-dict shape.
def generate_scr_narrative_offline(findings: dict) -> dict:
    rates = findings["return_rate_by_payment"]
    ranked = sorted(rates.items(), key=lambda kv: kv[1], reverse=True)
    top_name, top_rate = ranked[0]
    others = " and ".join(f"{v}% for {k}" for k, v in ranked[1:])

    seg = findings["highest_risk_segment"]
    peak = findings["true_peak_month"]
    infl = findings["outlier_inflated_month"]

    narrative = f"""SITUATION
Mamaearth's cleaned order data shows total revenue of INR {inr(findings['cleaned_total_revenue_inr'])}. The raw total of INR {inr(findings['raw_total_revenue_inr'])} was overstated by INR {inr(findings['duplicate_reconciliation_delta_inr'])}, a difference fully explained by duplicate (double-submit) orders removed during cleaning.

COMPLICATION
Returns are concentrated, not evenly spread. {top_name} orders return at {top_rate}%, versus {others}. The single highest-risk segment is {seg['payment_method']} orders in Tier-{seg['city_tier']} cities, at a {seg['return_rate_pct']}% return rate. Revenue reporting was also distorted: {month_label(infl['month'])} appeared to be the strongest month at INR {inr(infl['apparent_revenue_inr'])}, but two bulk orders inflated it. Corrected, {month_label(infl['month'])} revenue is INR {inr(infl['corrected_revenue_inr'])}.

RESOLUTION
Plan around {month_label(peak['month'])} as the genuine peak month, at INR {inr(peak['revenue_inr'])}. Regional ops should add order-confirmation and verification steps for {seg['payment_method']} orders in Tier-{seg['city_tier']} cities and incentivise prepaid payment there. Finance should report revenue on the cleaned basis (INR {inr(findings['cleaned_total_revenue_inr'])}) and exclude bulk-order outliers when judging monthly trends.
"""
    return {"status": "success", "narrative": narrative, "tokens": None}


# TASK 4b: Router. Use Gemini if a key exists and the call succeeds; otherwise use the offline path.
def get_narrative(findings: dict):
    result = generate_scr_narrative(findings , get_api_key())
    if result["status"] == "success":
        return result, "online"
    # print(f"[narrator] Online path unavailable ({result['message']}). Using offline fallback.")
    return generate_scr_narrative_offline(findings), "offline"


get_narrative(findings)

# TASK 5a: Checker. Five required figures must appear as substrings (after removing commas).
def _num(x):
    # 97358.3 -> "97358.3", 44.4 -> "44.4" (matches both "97358.30" and "97358.3" in the text)
    return f"{x:.2f}".rstrip("0").rstrip(".")


def check_figures(narrative: str, findings: dict) -> bool:
    text = narrative.replace(",", "")
    peak = findings["true_peak_month"]
    peak_month_name = calendar.month_name[int(peak["month"].split("-")[1])]

    required = [
        ("Cleaned total revenue",       _num(findings["cleaned_total_revenue_inr"])),
        ("COD return rate",             _num(findings["return_rate_by_payment"]["COD"])),
        ("Highest-risk segment rate",   _num(findings["highest_risk_segment"]["return_rate_pct"])),
        ("Duplicate delta",             _num(findings["duplicate_reconciliation_delta_inr"])),
        ("Peak month name",             peak_month_name),
        ("Peak month revenue",          _num(peak["revenue_inr"])),
    ]

    all_ok = True
    for label, needle in required:
        ok = needle in text
        all_ok = all_ok and ok
        print(f"{'PASS' if ok else 'FAIL'}  {label}: '{needle}'")
    # print("OVERALL:", "PASS" if all_ok else "FAIL")
    return all_ok


# TASK 5b: Entry point. Run the pipeline, save a sample, run the checker.
if __name__ == "__main__":
    findings = load_findings()

    # python narrator/generate_narrative.py --check narrator/sample_output.txt
    if len(sys.argv) == 3 and sys.argv[1] == "--check":
        check_figures(Path(sys.argv[2]).read_text(), findings)
        sys.exit(0)

    result, path = get_narrative(findings)
    # print(f"\n=== Narrative (path: {path}) ===\n")
    # print(result["narrative"])
    # print("\n=== Numeric accuracy check ===")
    check_figures(result["narrative"], findings)

    # Online output is saved as the graded sample; offline output is saved separately
    out_name = "sample_output.txt" if path == "online" else "sample_output_offline.txt"
    (BASE_DIR / out_name).write_text(result["narrative"])
    # print(f"\nSaved to narrator/{out_name}")
