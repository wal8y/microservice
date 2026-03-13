from __future__ import annotations

import logging
from typing import Dict, List

import httpx

from app.domain.models import ChapterMeta, Language, QuranCorpus, Verse
from app.infrastructure.settings import get_settings

logger = logging.getLogger(__name__)


LANG_FILE_MAP: Dict[str, str] = {
    "ar": "quran.json",
    "bn": "quran_bn.json",
    "en": "quran_en.json",
    "es": "quran_es.json",
    "fr": "quran_fr.json",
    "id": "quran_id.json",
    "ru": "quran_ru.json",
    "sv": "quran_sv.json",
    "tr": "quran_tr.json",
    "ur": "quran_ur.json",
    "zh": "quran_zh.json",
    "transliteration": "quran_transliteration.json",
}


async def load_quran_corpus() -> QuranCorpus:
    """
    Load Quran data for all configured languages from the CDN and assemble a QuranCorpus.
    """
    settings = get_settings()
    base = str(settings.quran_cdn_base)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Load Arabic base file for chapter metadata & Arabic verses
        ar_file = LANG_FILE_MAP["ar"]
        logger.info("Loading Quran base file from %s%s", base, ar_file)
        resp = await client.get(f"{base}{ar_file}")
        resp.raise_for_status()
        ar_data = resp.json()

        chapters_meta: Dict[int, ChapterMeta] = {}
        verses_by_lang: Dict[str, Dict[int, List[Verse]]] = {}

        # Arabic structure: list of chapters, each with "id", "revelation_place", "revelation_order", ...
        # and "verses": list of { "id": 1, "text": "...", ... }
        for chapter in ar_data:
            chapter_id = int(chapter["id"])
            chapters_meta[chapter_id] = ChapterMeta(
                id=chapter_id,
                revelation_place=chapter.get("revelation_place", ""),
                revelation_order=int(chapter.get("revelation_order", chapter_id)),
                name_arabic=chapter.get("name_arabic", ""),
                name_complex=chapter.get("name_complex", ""),
                name_simple=chapter.get("name_simple", ""),
                verses_count=len(chapter.get("verses", [])),
            )

            verses_by_lang.setdefault("ar", {})[chapter_id] = [
                Verse(
                    chapter_id=chapter_id,
                    verse_number=int(v["id"]),
                    text=v.get("text", ""),
                    language="ar",
                )
                for v in chapter.get("verses", [])
            ]

        # Load other languages, which are typically flat lists of verses with chapter/verse meta
        for lang, filename in LANG_FILE_MAP.items():
            if lang == "ar":
                continue
            logger.info("Loading Quran language file %s (%s)", filename, lang)
            resp_lang = await client.get(f"{base}{filename}")
            resp_lang.raise_for_status()
            verses_json = resp_lang.json()

            verses_by_chapter: Dict[int, List[Verse]] = {}
            for v in verses_json:
                chapter_id = int(v.get("chapter", v.get("chapterId", 0)))
                verse_id = int(v.get("verse", v.get("verseId", 0)))
                verses_by_chapter.setdefault(chapter_id, []).append(
                    Verse(
                        chapter_id=chapter_id,
                        verse_number=verse_id,
                        text=v.get("text", ""),
                        language=lang,
                    )
                )
            verses_by_lang[lang] = verses_by_chapter

        languages: Dict[str, Language] = {
            code: Language(code=code, name=code, source_file=filename)
            for code, filename in LANG_FILE_MAP.items()
        }

        corpus = QuranCorpus(
            languages=languages,
            chapters=chapters_meta,
            verses_by_lang=verses_by_lang,
        )
        logger.info(
            "Loaded Quran corpus with %d chapters and %d languages",
            len(chapters_meta),
            len(languages),
        )
        return corpus

