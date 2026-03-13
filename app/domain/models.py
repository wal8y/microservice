from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Language:
    code: str  # e.g. "ar", "en", "fr"
    name: str
    source_file: str  # underlying JSON filename from the CDN/dist


@dataclass(frozen=True)
class ChapterMeta:
    id: int
    revelation_place: str
    revelation_order: int
    name_arabic: str
    name_complex: str
    name_simple: str
    verses_count: int


@dataclass(frozen=True)
class Verse:
    chapter_id: int
    verse_number: int
    text: str
    language: str  # ISO code, e.g. "ar", "en"


@dataclass
class QuranCorpus:
    """
    Represents Quran content loaded into memory, across multiple languages.
    """

    languages: Dict[str, Language]
    chapters: Dict[int, ChapterMeta]
    verses_by_lang: Dict[str, Dict[int, List[Verse]]]  # lang -> chapter_id -> [verses]

    def get_chapter(self, chapter_id: int) -> Optional[ChapterMeta]:
        return self.chapters.get(chapter_id)

    def get_chapters(self) -> List[ChapterMeta]:
        return list(self.chapters.values())

    def get_verses(
        self, chapter_id: int, lang: str
    ) -> Optional[List[Verse]]:
        return self.verses_by_lang.get(lang, {}).get(chapter_id)

    def get_verse(
        self, chapter_id: int, verse_number: int, lang: str
    ) -> Optional[Verse]:
        verses = self.get_verses(chapter_id, lang)
        if not verses:
            return None
        for v in verses:
            if v.verse_number == verse_number:
                return v
        return None

