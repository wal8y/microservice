from typing import List, Optional

from app.domain.models import ChapterMeta, QuranCorpus, Verse


class QuranService:
    """
    Application service exposing Quran-related use-cases.
    """

    def __init__(self, corpus: QuranCorpus, default_lang: str = "ar"):
        self._corpus = corpus
        self._default_lang = default_lang

    def get_supported_languages(self) -> List[str]:
        return sorted(self._corpus.languages.keys())

    def resolve_lang(self, lang: Optional[str]) -> str:
        if lang and lang in self._corpus.languages:
            return lang
        return self._default_lang

    def list_chapters(self) -> List[ChapterMeta]:
        return sorted(self._corpus.get_chapters(), key=lambda c: c.id)

    def get_chapter(self, chapter_id: int) -> Optional[ChapterMeta]:
        return self._corpus.get_chapter(chapter_id)

    def get_chapter_verses(
        self, chapter_id: int, lang: Optional[str]
    ) -> Optional[List[Verse]]:
        lang_resolved = self.resolve_lang(lang)
        return self._corpus.get_verses(chapter_id, lang_resolved)

    def get_single_verse(
        self, chapter_id: int, verse_number: int, lang: Optional[str]
    ) -> Optional[Verse]:
        lang_resolved = self.resolve_lang(lang)
        return self._corpus.get_verse(chapter_id, verse_number, lang_resolved)

    def search(
        self, query: str, lang: Optional[str], limit: int = 20
    ) -> List[Verse]:
        if not query:
            return []
        lang_resolved = self.resolve_lang(lang)
        lowered = query.lower()
        results: List[Verse] = []
        verses_by_chapter = self._corpus.verses_by_lang.get(lang_resolved, {})
        for verses in verses_by_chapter.values():
            for verse in verses:
                if lowered in verse.text.lower():
                    results.append(verse)
                    if len(results) >= limit:
                        return results
        return results

