from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi import Query

from app.schemas.school import SchoolsList
from app.services import school as school_service
from app.services.http_client import HttpClientException

router = APIRouter()


@router.get("/", response_model=SchoolsList)
async def get_schools(
        limit: int = Query(default=10, ge=1, le=100, description="Numero di scuole da restituire (1-100)"),
        offset: int = Query(default=0, ge=0, description="Numero di scuole da saltare per la paginazione"),
        search: Optional[str] = Query(default=None, description="Termine di ricerca per filtrare le scuole per nome"),
        citta: Optional[str] = Query(default=None, description="Filtra per città"),
        provincia: Optional[str] = Query(default=None, description="Filtra per provincia"),
        indirizzo: Optional[str] = Query(default=None,
                                         description="Filtra per tipo di scuola (es. Liceo, informatico, ecc.)"),
        sort_by: str = Query(default="name", description="Campo per ordinamento (es. nome, città, provincia)"),
        order: str = Query(default="asc", regex="^(asc|desc)$", description="Ordine: asc o desc")
):
    """
    Recupera la lista delle scuole con opzioni di paginazione e filtro.

    Returns:
        dict: Lista delle scuole con metadati di paginazione
    """
    try:
        # Chiama il servizio per ottenere le scuole
        return await school_service.get_schools(
            limit=limit,
            offset=offset,
            search=search,
            citta=citta,
            provincia=provincia,
            indirizzo=indirizzo,
            sort_by=sort_by,
            order=order
        )



    except HttpClientException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "message": e.message,
                "stack": e.server_message,
                "url": e.url
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Parametri non validi",
                "stack": str(e),
                "url": None
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Internal Server Error",
                "stack": str(e),
                "url": None
            }
        )
