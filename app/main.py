import logging
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.application.quran_service import QuranService
from app.domain.models import QuranCorpus
from app.infrastructure.quran_loader import load_quran_corpus
from app.infrastructure.settings import get_settings
from app.interfaces.api.routes import router as api_router

logger = logging.getLogger(__name__)

app = FastAPI(title="Quran Microservice")

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

_corpus_cache: Optional[QuranCorpus] = None
_service_cache: Optional[QuranService] = None


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


@app.on_event("startup")
async def on_startup() -> None:
    configure_logging()
    logger.info("Starting %s in %s", settings.app_name, settings.environment)

    global _corpus_cache, _service_cache
    if _corpus_cache is None:
        _corpus_cache = await load_quran_corpus()
        _service_cache = QuranService(
            corpus=_corpus_cache, default_lang=settings.default_language
        )
        # store on app state so other modules can access without importing app.main
        app.state.quran_service = _service_cache


@app.get("/")
async def root():
    return {"message": "Quran Microservice. See /docs for API."}

