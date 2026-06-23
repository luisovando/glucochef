"""
Phase 8 — AI provider abstraction.

Single interface with one concrete implementation (OpenAI).
Internal-only at this phase — no routes or models are touched.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

_VALID_TRAFFIC_LIGHT_STATUSES = frozenset({"green", "amber", "red"})


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
        valid_labs = {
            kind: status
            for kind, status in latest_labs.items()
            if status in _VALID_TRAFFIC_LIGHT_STATUSES
        }
        if valid_labs:
            lab_lines = [f"- {kind}: {status}" for kind, status in valid_labs.items()]
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

_REDACT_PATTERNS = [
    (re.compile(r"(Allergies:\s*).+?\.", re.DOTALL), r"\1[REDACTED]."),
    (re.compile(r"(Intolerances:\s*).+?\.", re.DOTALL), r"\1[REDACTED]."),
    (re.compile(r"(diabetes type:\s*).+?(?=\\n|\.\b)", re.DOTALL), r"\1[REDACTED]"),
    (re.compile(r"(Dietary preferences:\s*).+?\.", re.DOTALL), r"\1[REDACTED]."),
]


def _redact_for_log(messages: list[dict[str, str]]) -> str:
    """Return a redacted version of the prompt for the AI usage log.

    Masks clinical profile fields (allergies, intolerances, diabetes type,
    dietary preferences) so sensitive patient context is not persisted in logs.
    Lab values are already traffic-light strings by design.
    """
    text = json.dumps(messages, indent=2)
    for pattern, replacement in _REDACT_PATTERNS:
        text = pattern.sub(replacement, text)
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
        if not self._api_key:
            raise ValueError(
                "AI API key is required. Set AI_API_KEY or OPENAI_API_KEY in .env"
            )
        self._client = AsyncOpenAI(api_key=self._api_key)

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
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.error("AI response is not valid JSON: %s", raw)
            raise ValueError("AI provider returned invalid JSON") from exc

        # Build the banned set (lowercase) for post-parse validation
        banned = {item.lower() for item in excluded}
        if profile.allergies:
            banned.update(a.lower() for a in profile.allergies)
        if profile.intolerances:
            banned.update(i.lower() for i in profile.intolerances)

        alternatives = [
            Alternative(
                ingredient=item["ingredient"],
                rationale=item["rationale"],
                rank=item["rank"],
            )
            for item in data
            if item.get("ingredient", "").lower() not in banned
        ]

        return alternatives

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
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.error("AI response is not valid JSON: %s", raw)
            raise ValueError("AI provider returned invalid JSON") from exc
