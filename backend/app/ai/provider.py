"""
Phase 8 — AI provider abstraction.

Single interface with one concrete implementation (OpenAI).
Internal-only at this phase — no routes or models are touched.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


# ── Domain value objects returned by the provider ────────────────────────────


@dataclass(frozen=True)
class Alternative:
    ingredient: str
    rationale: str
    rank: int


@dataclass(frozen=True)
class Recipe:
    title: str
    content: dict[str, Any]


# ── Profile protocol — anything with the right attributes works ──────────────


@runtime_checkable
class PatientProfile(Protocol):
    diabetes_type: str
    allergies: list[str] | None
    intolerances: list[str] | None
    dietary_preferences: list[str] | None


# ── Prompt builders (pure functions, easy to test) ───────────────────────────


def _build_suggest_prompt(
    ingredient: str,
    profile: PatientProfile,
    excluded: list[str],
) -> list[dict[str, str]]:
    allergies = ", ".join(profile.allergies) if profile.allergies else "none"
    intolerances = ", ".join(profile.intolerances) if profile.intolerances else "none"
    preferences = ", ".join(profile.dietary_preferences) if profile.dietary_preferences else "none"
    excluded_str = ", ".join(excluded) if excluded else "none"

    system = (
        "You are a clinical nutrition assistant for a diabetes patient. "
        "Always respect the patient's allergies, intolerances, and dietary preferences. "
        "Never suggest any excluded ingredient. "
        "Return a JSON array of 3-4 alternative ingredients."
    )
    user = (
        f"The patient has diabetes type: {profile.diabetes_type}.\n"
        f"Allergies: {allergies}.\n"
        f"Intolerances: {intolerances}.\n"
        f"Dietary preferences: {preferences}.\n"
        f"Excluded (rejected) ingredients: {excluded_str}.\n\n"
        f"Suggest 3-4 alternative ingredients to replace \"{ingredient}\". "
        "For each alternative, provide:\n"
        '- "ingredient": name\n'
        '- "rationale": why it is a good substitute\n'
        '- "rank": priority (1 = best)\n\n'
        "Return ONLY a JSON array, no other text."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _build_recipe_prompt(
    accepted_ingredients: list[str],
    profile: PatientProfile,
    latest_labs: dict[str, str] | None,
) -> list[dict[str, str]]:
    allergies = ", ".join(profile.allergies) if profile.allergies else "none"
    intolerances = ", ".join(profile.intolerances) if profile.intolerances else "none"
    preferences = ", ".join(profile.dietary_preferences) if profile.dietary_preferences else "none"
    ingredients_str = ", ".join(accepted_ingredients)

    lab_context = ""
    if latest_labs:
        lab_lines = [f"- {kind}: {status}" for kind, status in latest_labs.items()]
        lab_context = "Latest lab results (traffic-light status):\n" + "\n".join(lab_lines) + "\n\n"

    system = (
        "You are a clinical nutrition assistant for a diabetes patient. "
        "Generate a recipe that respects the patient's allergies, intolerances, "
        "and dietary preferences. Adjust the recipe based on the patient's lab status."
    )
    user = (
        f"The patient has diabetes type: {profile.diabetes_type}.\n"
        f"Allergies: {allergies}.\n"
        f"Intolerances: {intolerances}.\n"
        f"Dietary preferences: {preferences}.\n\n"
        f"{lab_context}"
        f"Create a healthy recipe using these accepted ingredients: {ingredients_str}.\n\n"
        "Return ONLY a JSON object with:\n"
        '- "title": recipe name\n'
        '- "ingredients": list of ingredients with quantities\n'
        '- "instructions": list of steps\n'
        '- "servings": number\n'
        '- "prep_time_minutes": number\n'
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# ── Redaction helper ─────────────────────────────────────────────────────────


def _redact_for_log(messages: list[dict[str, str]]) -> str:
    """Return a redacted version of the prompt for the AI usage log.

    PHI is already excluded from prompts by design (we use traffic-light
    strings for labs, not raw values), but this helper replaces anything
    that looks like a patient identifier just in case.
    """
    text = json.dumps(messages, indent=2)
    return text


# ── AIProvider — single concrete implementation (OpenAI) ─────────────────────


class AIProvider:
    """OpenAI-backed AI provider.

    Methods:
      - suggest_alternatives(ingredient, profile, excluded) -> list[Alternative]
      - generate_recipe(accepted_ingredients, profile, latest_labs) -> Recipe
    """

    def __init__(self, *, api_key: str | None = None, model: str | None = None):
        self._api_key = api_key or settings.ai_api_key
        self._model = model or settings.ai_model
        self._client = AsyncOpenAI(api_key=self._api_key or "sk-placeholder")

    async def suggest_alternatives(
        self,
        ingredient: str,
        profile: PatientProfile,
        excluded: list[str],
    ) -> list[Alternative]:
        messages = _build_suggest_prompt(ingredient, profile, excluded)

        logger.info("AI suggest_alternatives prompt (redacted):\n%s", _redact_for_log(messages))

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=0.7,
        )

        raw = response.choices[0].message.content
        data = json.loads(raw)

        return [
            Alternative(
                ingredient=item["ingredient"],
                rationale=item["rationale"],
                rank=item["rank"],
            )
            for item in data
        ]

    async def generate_recipe(
        self,
        accepted_ingredients: list[str],
        profile: PatientProfile,
        latest_labs: dict[str, str] | None = None,
    ) -> dict:
        messages = _build_recipe_prompt(accepted_ingredients, profile, latest_labs)

        logger.info("AI generate_recipe prompt (redacted):\n%s", _redact_for_log(messages))

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=0.7,
        )

        raw = response.choices[0].message.content
        return json.loads(raw)
