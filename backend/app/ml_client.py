import json
import logging
import re
import time

import httpx

from app.config import settings
from app.exceptions import MLServiceUnavailableError

logger = logging.getLogger("ml_service")

_LANGUAGE_NAMES = {
    "en": "English",
    "ru": "Russian",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "zh": "Chinese",
    "it": "Italian",
    "pt": "Portuguese",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "tr": "Turkish",
    "pl": "Polish",
    "nl": "Dutch",
    "sv": "Swedish",
    "uk": "Ukrainian",
    "cs": "Czech",
    "el": "Greek",
    "hi": "Hindi",
    "id": "Indonesian",
    "vi": "Vietnamese",
    "th": "Thai",
    "fi": "Finnish",
    "da": "Danish",
    "no": "Norwegian",
    "ro": "Romanian",
    "hu": "Hungarian",
}

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$")


# Изоляция ML-логики: вся работа с моделью инкапсулирована здесь.
# Остальной код (API, Celery-задачи) знает только про метод translate().
class MLTranslationService:
    def __init__(self) -> None:
        self._base_url = settings.vllm_base_url
        self._model = settings.model_name
        self._max_new_tokens = settings.ml_max_new_tokens
        self._timeout = settings.ml_request_timeout

    def _build_messages(self, text: str, source_lang: str, target_lang: str) -> list[dict]:
        tgt = _LANGUAGE_NAMES.get(target_lang, target_lang)

        # Автоопределение языка: просим модель самостоятельно распознать исходный язык
        # и вернуть строгий JSON с определённым языком и переводом одним вызовом.
        if source_lang == "auto":
            return [
                {
                    "role": "system",
                    "content": (
                        "You are a professional translator. First detect the language of the "
                        f"user's text, then translate it into {tgt}. Respond with strict JSON "
                        'only (no markdown, no code fences) in the exact form '
                        '{"detected_language": "<ISO 639-1 code, lowercase>", "translation": "<translated text only>"}.'
                    ),
                },
                {"role": "user", "content": text},
            ]

        src = _LANGUAGE_NAMES.get(source_lang, source_lang)
        return [
            {
                "role": "system",
                "content": (
                    f"You are a professional translator. Translate the user's text from "
                    f"{src} to {tgt}. Reply with the translation only, no explanations, "
                    f"no quotes, no extra commentary."
                ),
            },
            {"role": "user", "content": text},
        ]

    @staticmethod
    def _parse_auto_response(content: str) -> tuple[str | None, str]:
        cleaned = _CODE_FENCE_RE.sub("", content.strip()).strip()
        try:
            data = json.loads(cleaned)
            translation = str(data.get("translation", "")).strip()
            detected = data.get("detected_language")
            detected = str(detected).strip().lower() or None if detected else None
            if translation:
                return detected, translation
        except (ValueError, AttributeError):
            pass
        # Модель не вернула ожидаемый JSON — отдаём сырой ответ как перевод,
        # язык в этом случае остаётся неопределённым (используем исходное значение "auto")
        return None, cleaned

    async def translate(
        self, text: str, source_lang: str, target_lang: str, creativity: float
    ) -> tuple[str, str | None]:
        """Возвращает (переведённый_текст, определённый_язык_источника или None)."""
        stage_start = time.perf_counter()
        payload = {
            "model": self._model,
            "messages": self._build_messages(text, source_lang, target_lang),
            "temperature": creativity,
            # Управление ресурсами: ограничение длины генерации (max_new_tokens)
            "max_tokens": self._max_new_tokens,
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions", json=payload
                )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            logger.error("ml_service.translate_failed", extra={"error": str(exc)})
            raise MLServiceUnavailableError() from exc

        if source_lang == "auto":
            detected_lang, translated = self._parse_auto_response(content)
        else:
            detected_lang, translated = None, content

        elapsed_ms = (time.perf_counter() - stage_start) * 1000
        logger.info(
            "ml_service.translate_done",
            extra={
                "elapsed_ms": round(elapsed_ms, 1),
                "chars_in": len(text),
                "chars_out": len(translated),
                "detected_lang": detected_lang,
            },
        )
        return translated, detected_lang


ml_service = MLTranslationService()
