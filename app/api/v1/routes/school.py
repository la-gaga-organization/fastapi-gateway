from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi import Query

from app.schemas.school import SchoolsList, SchoolBase, SchoolGet
from app.services import school as school_service
from app.services.http_client import OrientatiException, OrientatiResponse

router = APIRouter()


@router.get("/", response_model=SchoolsList)
async def get_schools(
        limit: int = Query(default=10, ge=1, le=100, description="Numero di scuole da restituire (1-100)"),
        offset: int = Query(default=0, ge=0, description="Numero di scuole da saltare per la paginazione"),
        search: Optional[str] = Query(default=None, description="Termine di ricerca per filtrare le scuole per nome"),
        tipo: Optional[str] = Query(default=None, description="Filtra per tipo di scuola (es. Liceo, ITIS, ecc.)"),
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
            tipo=tipo,
            citta=citta,
            provincia=provincia,
            indirizzo=indirizzo,
            sort_by=sort_by,
            order=order
        )

    except OrientatiException as e:
        raise HTTPException(status_code=e.status_code,
                            detail={"message": e.message, "details": e.details, "url": e.url})


@router.get("/{school_id}", response_model=SchoolGet)
async def get_school(school_id: int):
    """
    Recupera i dettagli di una scuola specifica per ID.

    Args:
        school_id (int): ID della scuola da recuperare

    Returns:
        dict: Dettagli della scuola
    """
    try:
        school = await school_service.get_school_by_id(school_id)
        if not school:
            raise OrientatiException(
                status_code=404,
                message="School not found",
                details={"message": f"School with ID {school_id} not found"},
                url=f"/schools/{school_id}"
            )
        return SchoolGet(school)


    except OrientatiException as e:
        raise HTTPException(status_code=e.status_code,
                            detail={"message": e.message, "details": e.details, "url": e.url})

