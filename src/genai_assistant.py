"""
GenAI Support Insights Assistant Module
Module 7: Customer Support Ticket Analytics & GenAI Business Assistant

Generates grounded executive management reports from verified SQL analytics:
- Strictly injects verified database KPIs into the model prompt to prevent hallucinations
- Analyzes problem categories, resolution bottlenecks, and unresolved hotspots
- Suggests concrete operational actions based on observed trends
- Implements Google Gemini API integration (zero-cost free tier with official google-genai SDK)
- Provides a transparent, deterministic fallback reporter if no API key is provided
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from src.analytics import get_all_analytics_kpis, format_analytics_summary_text


@dataclass
class GenAIReportResult:
    """Standard container for AI executive reports."""
    content: str
    is_fallback: bool
    model_name: str
    disclaimer: str
    generation_time_seconds: float = 0.0
    metrics: Optional[Dict[str, Any]] = None


def build_grounded_prompt(kpis: Dict[str, Any]) -> str:
    """
    Constructs a strictly grounded prompt containing verified SQL metrics.
    Instructs the LLM to act as a senior support operations analyst without inventing figures.
    """
    metrics_digest = format_analytics_summary_text(kpis)

    return f"""You are a Senior Customer Support Operations Director and Executive Business Advisor.
Your objective is to turn the verified SQL analytics metrics below into an actionable, professional Management Support Insights Report.

CRITICAL GROUNDING RULES:
1. Rely EXCLUSIVELY on the verified metrics provided in the context below.
2. NEVER invent, extrapolate, or fabricate ticket counts, resolution hours, or backlog percentages.
3. If an explanation is an operational recommendation or hypothesis, explicitly state it as a recommendation.
4. Protect customer privacy: do not output any personal customer identifiers.

VERIFIED EVIDENCE FROM SQL DATABASE:
{metrics_digest}

REPORT STRUCTURE GUIDELINES:
Please format your response in clean GitHub-Flavored Markdown with the following clear sections:

### 1. Executive Summary
Brief high-level overview of overall ticket volume, current unresolved backlog rate, and operational health.

### 2. Major Complaint Domains & Bottlenecks
Analyze the highest volume categories (e.g. Delivery, Billing, Technical) and identify which categories have the highest unresolved backlog rates.

### 3. Resolution Performance & SLA Analysis
Review average resolution times across categories. Highlight domains taking the longest to resolve and explain what this means for operational efficiency.

### 4. Immediate Critical Attention Items
Highlight the top critical and high-priority unresolved tickets that require immediate escalation.

### 5. Recommended Operational Actions
Provide 3 to 4 concrete, actionable operational decisions based on the data (e.g. logistics partner review, developer bug escalation, automated billing refund policies, staffing adjustments).
"""


def generate_fallback_report(kpis: Dict[str, Any]) -> GenAIReportResult:
    """
    Generates a high-quality, deterministic template-driven management report
    directly from verified SQL metrics when no external GenAI model is available.
    """
    start_time = time.time()
    total = kpis.get("total_tickets", 0)
    unresolved = kpis.get("unresolved_tickets", 0)
    unresolved_pct = kpis.get("unresolved_rate_pct", 0.0)
    avg_hours = kpis.get("avg_resolution_hours", 0.0)
    critical_cnt = kpis.get("critical_unresolved_count", 0)
    high_cnt = kpis.get("high_unresolved_count", 0)

    # Top category
    cat_df = kpis.get("category_distribution", None)
    if cat_df is not None and not cat_df.empty:
        top_cat = cat_df.iloc[0]["category"]
        top_cat_cnt = cat_df.iloc[0]["ticket_count"]
        top_cat_pct = cat_df.iloc[0]["percentage"]
    else:
        top_cat, top_cat_cnt, top_cat_pct = "None", 0, 0.0

    # Top unresolved category
    unres_df = kpis.get("unresolved_by_category", None)
    if unres_df is not None and not unres_df.empty:
        worst_unres = unres_df.iloc[0]["category"]
        worst_unres_cnt = int(unres_df.iloc[0]["unresolved_tickets"])
        worst_unres_pct = unres_df.iloc[0]["unresolved_rate_pct"]
    else:
        worst_unres, worst_unres_cnt, worst_unres_pct = "None", 0, 0.0

    # Longest resolution category
    res_metrics = kpis.get("resolution_metrics", {})
    by_cat_res = res_metrics.get("by_category_df", None)
    if by_cat_res is not None and not by_cat_res.empty:
        slowest_cat = by_cat_res.iloc[0]["category"]
        slowest_hours = by_cat_res.iloc[0]["avg_resolution_hours"]
    else:
        slowest_cat, slowest_hours = "None", 0.0

    summary_metrics = {
        "total_tickets": int(total),
        "unresolved_tickets": int(unresolved),
        "unresolved_rate_pct": float(unresolved_pct),
        "avg_resolution_hours": float(avg_hours),
        "critical_unresolved_count": int(critical_cnt),
        "high_unresolved_count": int(high_cnt),
    }

    report_lines = [
        "# Executive Support Insights Management Report",
        "",
        "## 1. Executive Summary",
        f"The support organization has received **{total} customer tickets** to date. Currently, **{unresolved} tickets remain unresolved** representing a **{unresolved_pct}% backlog rate** across all operations. The fleet-wide average ticket resolution time is **{avg_hours} hours**.",
        "",
        "## 2. Major Complaint Domains & Backlog Hotspots",
    ]

    if worst_unres == top_cat and top_cat != "None":
        report_lines.append(
            f"- **Primary Inbound & Backlog Hotspot:** **{top_cat}** represents both the largest complaint category with **{top_cat_cnt} tickets ({top_cat_pct}%)** and the highest unresolved volume with **{worst_unres_cnt} open/pending tickets** ({worst_unres_pct}% backlog rate)."
        )
    else:
        report_lines.extend([
            f"- **Primary Inbound Category:** **{top_cat}** represents the single largest complaint category with **{top_cat_cnt} tickets ({top_cat_pct}%)** of all customer inquiries.",
            f"- **Primary Backlog Bottleneck:** **{worst_unres}** carries the highest unresolved volume with **{worst_unres_cnt} open/pending tickets**, constituting an alarming **{worst_unres_pct}% unresolved rate** for that category.",
        ])

    report_lines.extend([
        "",
        "## 3. Resolution Performance & SLA Analysis",
        f"- **Overall Mean Resolution:** Resolved issues take an average of **{avg_hours} hours** from creation to closure.",
        f"- **Slowest Resolution Domain:** **{slowest_cat}** tickets require the longest turnaround at an average of **{slowest_hours} hours**.",
        "",
        "## 4. Immediate Critical Attention Items",
        f"There are currently **{critical_cnt} Critical** and **{high_cnt} High** priority tickets awaiting resolution in the backlog.",
    ])

    urgent_df = kpis.get("management_attention_tickets", None)
    if urgent_df is not None and not urgent_df.empty:
        report_lines.append("\n**Top Priority Escalations:**")
        for _, row in urgent_df.head(4).iterrows():
            report_lines.append(f"- **[{row['priority']}]** `{row['ticket_id']}` ({row['category']}): {row['subject']}")

    # Grounded operational recommendations directly tied to verified database metrics
    action_items = [
        f"1. **Triage Backlog in {worst_unres}:** Reallocate support tier resources to address the {worst_unres_cnt} unresolved tickets in {worst_unres} ({worst_unres_pct}% backlog rate).",
        f"2. **Streamline Inbound Inquiries for {top_cat}:** Review self-service knowledge base resources and intake routing for {top_cat} to mitigate the highest incoming volume domain ({top_cat_pct}% of inquiries).",
        f"3. **Investigate SLA Delays in {slowest_cat}:** Review workflow bottlenecks in {slowest_cat} to improve the current {slowest_hours}-hour average turnaround time.",
    ]

    if critical_cnt > 0:
        action_items.append(f"4. **Expedite Critical Blockers:** Immediately route the {critical_cnt} critical priority unresolved tickets to senior escalations to meet customer SLAs.")
    elif high_cnt > 0:
        action_items.append(f"4. **Address High-Priority Queue:** Prioritize the {high_cnt} high-priority open tickets to prevent backlog aging.")
    else:
        action_items.append("4. **Sustain Resolution Cadence:** Maintain current triage standards as zero critical or high-priority tickets are currently blocked.")

    report_lines.extend([
        "",
        "## 5. Recommended Operational Actions",
        *action_items
    ])

    elapsed = round(time.time() - start_time, 3)
    return GenAIReportResult(
        content="\n".join(report_lines),
        is_fallback=True,
        model_name="Deterministic Analytical Template Engine",
        disclaimer="Report generated via deterministic template fallback grounded strictly in SQLite query results.",
        generation_time_seconds=elapsed,
        metrics=summary_metrics
    )


def generate_support_insights_report(
    kpis: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None
) -> GenAIReportResult:
    """
    Main entry point for AI report generation:
    1. Obtains analytical KPIs from Module 5.
    2. Attempts generation via Google Gemini API if GEMINI_API_KEY is present.
    3. Falls back gracefully and honestly to deterministic template reporting if no key or error occurs.
    """
    if kpis is None:
        kpis = get_all_analytics_kpis(db_path=db_path)

    summary_metrics = {
        "total_tickets": int(kpis.get("total_tickets", 0)),
        "unresolved_tickets": int(kpis.get("unresolved_tickets", 0)),
        "unresolved_rate_pct": float(kpis.get("unresolved_rate_pct", 0.0)),
        "avg_resolution_hours": float(kpis.get("avg_resolution_hours", 0.0)),
        "critical_unresolved_count": int(kpis.get("critical_unresolved_count", 0)),
        "high_unresolved_count": int(kpis.get("high_unresolved_count", 0)),
    }

    if kpis.get("total_tickets", 0) == 0:
        return GenAIReportResult(
            content="### No Ticket Data Available\n\nNo customer support ticket records were found in the database. Please ingest a CSV file or API payload first.",
            is_fallback=True,
            model_name="N/A",
            disclaimer="No data to analyze.",
            metrics=summary_metrics
        )

    # Check for Gemini API key
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not gemini_key:
        return generate_fallback_report(kpis)

    # Attempt GenAI Call using official google-genai SDK
    start_time = time.time()
    try:
        from google import genai

        client = genai.Client(api_key=gemini_key)
        prompt = build_grounded_prompt(kpis)

        # Use gemini-2.5-flash or gemini-1.5-flash
        model_id = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        response = client.models.generate_content(
            model=model_id,
            contents=prompt,
        )

        elapsed = round(time.time() - start_time, 2)
        return GenAIReportResult(
            content=response.text,
            is_fallback=False,
            model_name=f"Google Gemini ({model_id})",
            disclaimer=f"AI analysis generated by {model_id} strictly grounded in SQLite analytics.",
            generation_time_seconds=elapsed,
            metrics=summary_metrics
        )

    except Exception as e:
        # If API call fails (rate limit, network issue, invalid key), fall back gracefully
        fallback_res = generate_fallback_report(kpis)
        fallback_res.disclaimer = (
            f"GenAI API attempt failed ({type(e).__name__}: {str(e)}). "
            "Fell back automatically to deterministic analytical report."
        )
        return fallback_res


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 65)
    print("AI SUPPORT INSIGHTS ASSISTANT DEMONSTRATION")
    print("=" * 65)
    report_result = generate_support_insights_report()
    print(f"\nModel Utilized: {report_result.model_name}")
    print(f"Fallback Mode : {report_result.is_fallback}")
    print(f"Generation Time: {report_result.generation_time_seconds}s\n")
    print(report_result.content)
    print("=" * 65)
