from ui.tui import _model_choices


def test_model_choices_cover_configured_provider_catalog_and_current_model():
    choices = _model_choices([
        {
            "name": "Groq",
            "base_url": "https://api.groq.com/openai/v1",
            "model": "custom-groq-model",
        }
    ])
    models = [model for _, _, model in choices]
    assert choices[0] == ("Groq  ·  custom-groq-model", "Groq", "custom-groq-model")
    assert "llama-3.3-70b-versatile" in models
    assert len(models) == len(set(models))
