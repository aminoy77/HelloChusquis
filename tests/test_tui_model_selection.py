import asyncio

from ui.tui import HelloChusquisTUI, ModelPicker, _model_choices


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


def test_f2_opens_model_picker():
    async def exercise_picker():
        app = HelloChusquisTUI(config={
            "providers": [{
                "name": "Groq",
                "base_url": "https://api.groq.com/openai/v1",
                "model": "llama-3.3-70b-versatile",
            }]
        })
        async with app.run_test() as pilot:
            await pilot.press("f2")
            assert isinstance(app.screen, ModelPicker)
            await pilot.press("escape")

    asyncio.run(exercise_picker())
