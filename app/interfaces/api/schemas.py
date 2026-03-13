from typing import List, Optional

from pydantic import BaseModel


class LanguageOut(BaseModel):
    code: str
    name: str


class ChapterOut(BaseModel):
    id: int
    revelation_place: str
    revelation_order: int
    name_arabic: str
    name_complex: str
    name_simple: str
    verses_count: int


class VerseOut(BaseModel):
    chapter_id: int
    verse_number: int
    text: str
    language: str


class SearchResponse(BaseModel):
    query: str
    lang: str
    results: List[VerseOut]


class HealthResponse(BaseModel):
    status: str
    environment: str
    app_name: str

