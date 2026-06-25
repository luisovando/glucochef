"""
Phase 8 — AI provider abstraction.

AC1: Mocked HTTP client asserts the prompt structure includes the patient's
     allergies and excludes rejected ingredients.
"""

import json
from dataclasses import dataclass
from unittest.mock import AsyncMock, patch

import pytest


# ── Lightweight stand-ins for domain objects passed to the provider ──────────


@dataclass
class FakeProfile:
    diabetes_type: str = "type_2"
    allergies: list[str] | None = None
    intolerances: list[str] | None = None
    dietary_preferences: list[str] | None = None


# ── Tests ────────────────────────────────────────────────────────────────────


def _mock_openai_response(content: str):
    """Build a mock that looks like openai.chat.completions.create() return."""
    choice = type("Choice", (), {"message": type("Msg", (), {"content": content})()})()
    return type("Resp", (), {"choices": [choice]})()


class TestSuggestAlternatives:
    """AC1 — suggest_alternatives prompt includes allergies and excludes rejected."""

    async def test_prompt_includes_allergies_and_excludes_rejected(self):
        from app.ai.provider import AIProvider

        profile = FakeProfile(
            allergies=["peanuts", "shellfish"],
            intolerances=["lactose"],
            dietary_preferences=["Mediterranean"],
        )
        excluded = ["salmon", "shrimp"]

        mock_response = _mock_openai_response(json.dumps([
            {"ingredient": "tofu", "rationale": "High protein, allergy-safe", "rank": 1},
            {"ingredient": "chicken breast", "rationale": "Lean protein", "rank": 2},
            {"ingredient": "lentils", "rationale": "Plant-based protein", "rank": 3},
        ]))

        provider = AIProvider(api_key="sk-test-key")

        with patch.object(
            provider._client.chat.completions, "create", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_create:
            result = await provider.suggest_alternatives(
                ingredient="salmon",
                profile=profile,
                excluded=excluded,
            )

            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args
            messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages") or call_kwargs[0][0]

            # Flatten all message content into one string for assertion
            prompt_text = " ".join(
                m["content"] for m in messages if isinstance(m.get("content"), str)
            )

            # AC1a: prompt includes the patient's allergies
            assert "peanuts" in prompt_text, "Prompt must mention allergy: peanuts"
            assert "shellfish" in prompt_text, "Prompt must mention allergy: shellfish"

            # AC1b: prompt excludes rejected ingredients
            assert "salmon" in prompt_text, "Prompt must mention excluded ingredient: salmon"
            assert "shrimp" in prompt_text, "Prompt must mention excluded ingredient: shrimp"

            # Result should be a list of alternatives
            assert isinstance(result, list)
            assert len(result) >= 1

    async def test_filters_out_banned_ingredients_from_response(self):
        """Alternatives matching excluded/allergens/intolerances are filtered."""
        from app.ai.provider import AIProvider

        profile = FakeProfile(
            allergies=["peanuts"],
            intolerances=["lactose"],
        )
        excluded = ["salmon"]

        mock_response = _mock_openai_response(json.dumps([
            {"ingredient": "tofu", "rationale": "Safe", "rank": 1},
            {"ingredient": "Salmon", "rationale": "Oops", "rank": 2},
            {"ingredient": "Peanuts", "rationale": "Oops", "rank": 3},
        ]))

        provider = AIProvider(api_key="sk-test-key")

        with patch.object(
            provider._client.chat.completions, "create", new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await provider.suggest_alternatives(
                ingredient="salmon",
                profile=profile,
                excluded=excluded,
            )

            assert len(result) == 1
            assert result[0].ingredient == "tofu"


class TestGenerateRecipe:
    """AC1 — generate_recipe prompt includes allergies, intolerances, ingredients, and lab context."""

    async def test_prompt_includes_allergies_intolerances_ingredients_and_labs(self):
        """Prompt includes allergies, intolerances, accepted ingredients, and lab context."""
        from app.ai.provider import AIProvider

        profile = FakeProfile(
            allergies=["peanuts"],
            intolerances=["gluten"],
        )
        accepted_ingredients = ["chicken breast", "rice", "broccoli"]
        latest_labs = {"hba1c": "green", "fasting_glucose": "amber"}

        mock_response = _mock_openai_response(json.dumps({
            "title": "Grilled Chicken with Rice and Broccoli",
            "ingredients": ["chicken breast", "rice", "broccoli", "olive oil"],
            "instructions": ["Season the chicken...", "Cook rice...", "Steam broccoli..."],
            "servings": 2,
            "prep_time_minutes": 30,
        }))

        provider = AIProvider(api_key="sk-test-key")

        with patch.object(
            provider._client.chat.completions, "create", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_create:
            result = await provider.generate_recipe(
                accepted_ingredients=accepted_ingredients,
                profile=profile,
                latest_labs=latest_labs,
            )

            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args
            messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages") or call_kwargs[0][0]

            prompt_text = " ".join(
                m["content"] for m in messages if isinstance(m.get("content"), str)
            )

            # AC1a: prompt includes the patient's allergies
            assert "peanuts" in prompt_text, "Prompt must mention allergy: peanuts"

            # AC1b: prompt includes intolerances
            assert "gluten" in prompt_text, "Prompt must mention intolerance: gluten"

            # AC1c: prompt includes accepted ingredients
            assert "chicken breast" in prompt_text
            assert "rice" in prompt_text

            # AC1d: prompt includes lab context
            assert "hba1c" in prompt_text.lower() or "HbA1c" in prompt_text

            # Result should be a dict with recipe data
            assert isinstance(result, dict)
            assert "title" in result

    async def test_invalid_lab_values_excluded_from_prompt(self):
        """Raw numeric lab values are filtered out; only traffic-light strings pass."""
        from app.ai.provider import AIProvider

        profile = FakeProfile(allergies=["peanuts"])
        accepted_ingredients = ["rice"]
        latest_labs = {"hba1c": "green", "fasting_glucose": "8.4%"}

        mock_response = _mock_openai_response(json.dumps({
            "title": "Rice Bowl",
            "ingredients": ["rice"],
            "instructions": ["Cook rice"],
            "servings": 1,
            "prep_time_minutes": 15,
        }))

        provider = AIProvider(api_key="sk-test-key")

        with patch.object(
            provider._client.chat.completions, "create", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_create:
            await provider.generate_recipe(
                accepted_ingredients=accepted_ingredients,
                profile=profile,
                latest_labs=latest_labs,
            )

            call_kwargs = mock_create.call_args
            messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages") or call_kwargs[0][0]
            prompt_text = " ".join(
                m["content"] for m in messages if isinstance(m.get("content"), str)
            )

            assert "8.4%" not in prompt_text, "Raw lab value must not appear in prompt"
            assert "hba1c" in prompt_text.lower(), "Valid traffic-light lab should be present"
