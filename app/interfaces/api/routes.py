from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.application.quran_service import QuranService
from app.infrastructure.settings import get_settings
from app.interfaces.api.schemas import (
    ChapterOut,
    HealthResponse,
    LanguageOut,
    SearchResponse,
    VerseOut,
)

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok", environment=settings.environment, app_name=settings.app_name
    )


def get_quran_service(request: Request) -> QuranService:
    service = getattr(request.app.state, "quran_service", None)
    if service is None:
        raise HTTPException(status_code=500, detail="Quran service not initialized")
    return service


@router.get("/languages", response_model=List[LanguageOut], tags=["quran"])
async def list_languages(
    service: QuranService = Depends(get_quran_service),
) -> List[LanguageOut]:
    langs = service.get_supported_languages()
    return [LanguageOut(code=l, name=l) for l in langs]


@router.get("/chapters", response_model=List[ChapterOut], tags=["quran"])
async def list_chapters(
    service: QuranService = Depends(get_quran_service),
) -> List[ChapterOut]:
    chapters = service.list_chapters()
    return [
        ChapterOut(
            id=c.id,
            revelation_place=c.revelation_place,
            revelation_order=c.revelation_order,
            name_arabic=c.name_arabic,
            name_complex=c.name_complex,
            name_simple=c.name_simple,
            verses_count=c.verses_count,
        )
        for c in chapters
    ]


@router.get("/chapters/{chapter_id}", response_model=ChapterOut, tags=["quran"])
async def get_chapter(
    chapter_id: int,
    service: QuranService = Depends(get_quran_service),
) -> ChapterOut:
    chapter = service.get_chapter(chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return ChapterOut(
        id=chapter.id,
        revelation_place=chapter.revelation_place,
        revelation_order=chapter.revelation_order,
        name_arabic=chapter.name_arabic,
        name_complex=chapter.name_complex,
        name_simple=chapter.name_simple,
        verses_count=chapter.verses_count,
    )


@router.get(
    "/chapters/{chapter_id}/verses",
    response_model=List[VerseOut],
    tags=["quran"],
)
async def get_chapter_verses(
    chapter_id: int,
    lang: Optional[str] = Query(None, description="Language code, e.g. en, fr, ar"),
    service: QuranService = Depends(get_quran_service),
) -> List[VerseOut]:
    verses = service.get_chapter_verses(chapter_id, lang)
    if verses is None:
        raise HTTPException(status_code=404, detail="Chapter or language not found")
    return [
        VerseOut(
            chapter_id=v.chapter_id,
            verse_number=v.verse_number,
            text=v.text,
            language=v.language,
        )
        for v in verses
    ]


@router.get(
    "/verses/{chapter_id}/{verse_number}",
    response_model=VerseOut,
    tags=["quran"],
)
async def get_verse(
    chapter_id: int,
    verse_number: int,
    lang: Optional[str] = Query(None, description="Language code, e.g. en, fr, ar"),
    service: QuranService = Depends(get_quran_service),
) -> VerseOut:
    verse = service.get_single_verse(chapter_id, verse_number, lang)
    if verse is None:
        raise HTTPException(status_code=404, detail="Verse not found")
    return VerseOut(
        chapter_id=verse.chapter_id,
        verse_number=verse.verse_number,
        text=verse.text,
        language=verse.language,
    )


@router.get("/search", response_model=SearchResponse, tags=["quran"])
async def search(
    q: str = Query(..., min_length=2, description="Search text"),
    lang: Optional[str] = Query(None, description="Language code, e.g. en, fr, ar"),
    limit: int = Query(20, ge=1, le=100),
    service: QuranService = Depends(get_quran_service),
) -> SearchResponse:
    results = service.search(q, lang, limit=limit)
    lang_resolved = service.resolve_lang(lang)
    return SearchResponse(
        query=q,
        lang=lang_resolved,
        results=[
            VerseOut(
                chapter_id=v.chapter_id,
                verse_number=v.verse_number,
                text=v.text,
                language=v.language,
            )
            for v in results
        ],
    )

