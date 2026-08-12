"""Streamlit application smoke test."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_app_starts_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = Path(__file__).resolve().parents[1] / "app.py"
    test = AppTest.from_file(str(app), default_timeout=30).run()
    assert not test.exception
    assert any("DEMO DATA" in warning.value for warning in test.warning)
    assert any("Overview" in title.value for title in test.header)
    for section in ["Data Exploration", "AI Assistant", "Advanced Analytics", "Data Quality & Performance", "Report Export"]:
        test.sidebar.radio[0].set_value(section)
        test.run()
        assert not test.exception, f"Section failed: {section}"
        if section == "AI Assistant":
            labels = [button.label for button in test.button]
            assert "💡 Generate Commerce Insights" in labels
            assert "▶ Run Verified Task" in labels
            assert any(area.key == "ai_query_draft" for area in test.text_area)
