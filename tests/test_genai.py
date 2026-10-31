"""
Unit Tests for GenAI Support Insights Assistant Module
Module 7: Customer Support Ticket Analytics & GenAI Business Assistant
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.genai_assistant import (
    build_grounded_prompt,
    generate_fallback_report,
    generate_support_insights_report,
    GenAIReportResult,
)


@pytest.fixture
def sample_kpis():
    """Provides verified mock KPIs matching Module 5 output."""
    category_df = pd.DataFrame([
        {"category": "Delivery & Shipping", "ticket_count": 20, "percentage": 40.0},
        {"category": "Technical Support", "ticket_count": 15, "percentage": 30.0},
        {"category": "Billing & Refunds", "ticket_count": 15, "percentage": 30.0},
    ])
    status_df = pd.DataFrame([
        {"status": "Resolved", "ticket_count": 30, "percentage": 60.0},
        {"status": "Open", "ticket_count": 15, "percentage": 30.0},
        {"status": "Pending", "ticket_count": 5, "percentage": 10.0},
    ])
    unresolved_df = pd.DataFrame([
        {
            "category": "Technical Support",
            "total_tickets": 15,
            "unresolved_tickets": 10,
            "resolved_tickets": 5,
            "unresolved_rate_pct": 66.67
        },
        {
            "category": "Delivery & Shipping",
            "total_tickets": 20,
            "unresolved_tickets": 6,
            "resolved_tickets": 14,
            "unresolved_rate_pct": 30.0
        },
        {
            "category": "Billing & Refunds",
            "total_tickets": 15,
            "unresolved_tickets": 4,
            "resolved_tickets": 11,
            "unresolved_rate_pct": 26.67
        },
    ])
    by_cat_res = pd.DataFrame([
        {"category": "Technical Support", "resolved_count": 5, "avg_resolution_hours": 24.5},
        {"category": "Delivery & Shipping", "resolved_count": 14, "avg_resolution_hours": 12.0},
        {"category": "Billing & Refunds", "resolved_count": 11, "avg_resolution_hours": 6.5},
    ])
    urgent_df = pd.DataFrame([
        {
            "ticket_id": "TKT-TEST-CRIT",
            "priority": "Critical",
            "category": "Technical Support",
            "status": "Open",
            "created_at": "2026-03-01 10:00:00",
            "subject": "Core service down",
            "description": "500 errors on authentication"
        }
    ])

    return {
        "total_tickets": 50,
        "open_tickets": 15,
        "pending_tickets": 5,
        "resolved_tickets": 30,
        "closed_tickets": 0,
        "unresolved_tickets": 20,
        "unresolved_rate_pct": 40.0,
        "avg_resolution_hours": 14.33,
        "critical_unresolved_count": 1,
        "high_unresolved_count": 0,
        "category_distribution": category_df,
        "status_distribution": status_df,
        "resolution_metrics": {
            "overall_avg_hours": 14.33,
            "by_category_df": by_cat_res
        },
        "unresolved_by_category": unresolved_df,
        "volume_trends": pd.DataFrame(),
        "management_attention_tickets": urgent_df
    }


def test_build_grounded_prompt(sample_kpis):
    """Verifies that grounded prompt incorporates exact SQL metrics and anti-hallucination rules."""
    prompt = build_grounded_prompt(sample_kpis)
    assert "CRITICAL GROUNDING RULES" in prompt
    assert "50" in prompt  # Total tickets
    assert "14.33" in prompt  # Avg resolution hours
    assert "Technical Support" in prompt
    assert "Delivery & Shipping" in prompt


def test_generate_fallback_report(sample_kpis):
    """Verifies deterministic fallback generation without external API."""
    result = generate_fallback_report(sample_kpis)
    assert isinstance(result, GenAIReportResult)
    assert result.is_fallback is True
    assert "Deterministic Analytical" in result.model_name
    assert "50 customer tickets" in result.content
    assert "20 tickets remain unresolved" in result.content
    assert "40.0% backlog rate" in result.content
    assert "14.33 hours" in result.content
    assert "Delivery & Shipping" in result.content
    assert "Technical Support" in result.content
    assert "TKT-TEST-CRIT" in result.content


def test_empty_kpis_handling():
    """Verifies handling when zero tickets are available in database."""
    empty_kpis = {"total_tickets": 0}
    result = generate_support_insights_report(kpis=empty_kpis)
    assert "No Ticket Data Available" in result.content
    assert result.is_fallback is True


def test_simulated_gemini_api_call(sample_kpis):
    """Verifies successful API calling flow when GEMINI_API_KEY is configured."""
    mock_response = MagicMock()
    mock_response.text = "## AI Insights Report\nGenerated successfully by Gemini 2.5."

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict("os.environ", {"GEMINI_API_KEY": "fake-test-key-123"}):
        with patch("google.genai.Client", return_value=mock_client):
            result = generate_support_insights_report(kpis=sample_kpis)
            assert result.is_fallback is False
            assert "Google Gemini" in result.model_name
            assert "AI Insights Report" in result.content


def test_gemini_api_exception_fallback(sample_kpis):
    """Verifies graceful fallback to deterministic report when API call raises an exception."""
    with patch.dict("os.environ", {"GEMINI_API_KEY": "fake-test-key-123"}):
        with patch("google.genai.Client", side_effect=RuntimeError("API quota exceeded or network down")):
            result = generate_support_insights_report(kpis=sample_kpis)
            assert result.is_fallback is True
            assert "Deterministic Analytical" in result.model_name
            assert "50 customer tickets" in result.content
            assert "Fell back automatically" in result.disclaimer
