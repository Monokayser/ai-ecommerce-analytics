"""Streamlit application smoke test."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from config.version import APP_RELEASE


def _open_ai_assistant(test: AppTest) -> AppTest:
    navigation = next(radio for radio in test.radio if radio.key == "current_section")
    navigation.set_value("AI Assistant")
    return test.run()


def _button(test: AppTest, label: str):
    return next(button for button in test.button if button.label == label)


def test_app_starts_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = Path(__file__).resolve().parents[1] / "app.py"
    test = AppTest.from_file(str(app), default_timeout=30).run()
    assert not test.exception
    assert any("DEMO DATA" in warning.value for warning in test.warning)
    assert any("Overview" in title.value for title in test.header)
    for section in ["Data Exploration", "AI Assistant", "Advanced Analytics", "Data Quality & Performance", "Report Export"]:
        navigation = next(radio for radio in test.radio if radio.key == "current_section")
        navigation.set_value(section)
        test.run()
        assert not test.exception, f"Section failed: {section}"
        if section == "AI Assistant":
            labels = [button.label for button in test.button]
            assert "💡 Generate Commerce Insights" in labels
            assert "Run task autonomously" in labels
            assert any(area.key == "ai_query_draft" for area in test.text_area)


def test_app_exposes_release_marker_and_navigation_reset(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    app = Path(__file__).resolve().parents[1] / "app.py"
    test = AppTest.from_file(str(app), default_timeout=30).run()
    navigation = next(radio for radio in test.radio if radio.key == "current_section")
    assert [label.split("  ", 1)[-1] for label in navigation.options] == [
        "Overview", "Explore data", "Ask AI", "Advanced", "Quality & speed", "Export reports"
    ]
    html = " ".join(item.value for item in test.markdown)
    assert f"data-app-version=\"{APP_RELEASE}\"" in html


def test_ai_composer_validates_an_empty_question(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    app = Path(__file__).resolve().parents[1] / "app.py"
    test = _open_ai_assistant(AppTest.from_file(str(app), default_timeout=30).run())

    _button(test, "Run task autonomously").click()
    test.run()

    assert not test.exception
    assert any("Describe the outcome you want" in warning.value for warning in test.warning)


def test_ai_composer_runs_saves_and_resets_a_verified_local_answer(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    app = Path(__file__).resolve().parents[1] / "app.py"
    test = _open_ai_assistant(AppTest.from_file(str(app), default_timeout=45).run())
    question = "Compare total sales by region from highest to lowest."

    next(area for area in test.text_area if area.key == "ai_query_draft").set_value(question)
    _button(test, "Run task autonomously").click()
    test.run()

    assert not test.exception
    assert test.session_state["last_ai"]["question"] == question
    assert len(test.session_state["conversation"]) == 1
    html = " ".join(item.value for item in test.markdown)
    assert "Verified assistant answer" in html
    assert "Autonomous task completed" in html
    assert "You asked" in html
    assert question in html

    _button(test, "Save response").click()
    test.run()
    assert len(test.session_state["saved_ai_responses"]) == 1

    _button(test, "Reset agent").click()
    test.run()
    assert "last_ai" not in test.session_state
    assert "conversation" not in test.session_state
    assert "saved_ai_responses" not in test.session_state


def test_global_agent_launcher_routes_to_the_task_workspace(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    app = Path(__file__).resolve().parents[1] / "app.py"
    test = AppTest.from_file(str(app), default_timeout=30).run()

    html = " ".join(item.value for item in test.markdown)
    assert 'class="agent-launcher"' in html
    assert 'href="?assistant=1"' in html
    assert 'aria-label="Open the AI analytics agent"' in html

    test.query_params["assistant"] = "1"
    test.run()
    navigation = next(radio for radio in test.radio if radio.key == "current_section")
    assert navigation.value == "AI Assistant"
    html = " ".join(item.value for item in test.markdown)
    assert "Autonomous Analytics Agent" in html
    assert 'aria-label="Jump to the AI task composer"' in html
