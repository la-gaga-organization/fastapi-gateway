from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr
from app.services.http_client import OrientatiResponse


class SchoolAddress(BaseModel):  # indirizzo di studio
    nome: str
    descrizione: str | None = None
    materie: List[str] = []  # materie insegnate in questo indirizzo


class SchoolBase(BaseModel):
    nome: str
    tipo: str
    indirizzo: str
    città: str
    provincia: str
    codice_postale: str
    email_contatto: EmailStr
    telefono_contatto: str
    indirizzi_scuola: List[SchoolAddress] = []
    sito_web: str | None = None
    descrizione: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SchoolCreate(SchoolBase):
    pass

class SchoolGet(OrientatiResponse):
    def __init__(self, school: SchoolBase):
        self.nome = school.nome
        self.tipo = school.tipo
        self.indirizzo = school.indirizzo
        self.città = school.città
        self.provincia = school.provincia
        self.codice_postale = school.codice_postale
        self.email_contatto = school.email_contatto
        self.telefono_contatto = school.telefono_contatto
        self.indirizzi_scuola = school.indirizzi_scuola
        self.sito_web = school.sito_web
        self.descrizione = school.descrizione
        self.created_at = school.created_at
        self.updated_at = school.updated_at
        school_data = {
            "nome": self.nome,
            "tipo": self.tipo,
            "indirizzo": self.indirizzo,
            "città": self.città,
            "provincia": self.provincia,
            "codice_postale": self.codice_postale,
            "email_contatto": self.email_contatto,
            "telefono_contatto": self.telefono_contatto,
            "indirizzi_scuola": self.indirizzi_scuola,
            "sito_web": self.sito_web,
            "descrizione": self.descrizione,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        super().__init__(status_code=200, data=school_data)


class SchoolUpdate(SchoolBase):
    pass


class SchoolsList(OrientatiResponse):
    def __init__(
        self,
        status_code: int,
        scuole: List[SchoolCreate],
        total: int,
        limit: int,
        offset: int,
        filter_search: str | None = None,
        filter_tipo: str | None = None,
        filter_citta: str | None = None,
        filter_provincia: str | None = None,
        filter_indirizzo: str | None = None,
        sort_by: str | None = None,
        order: str | None = None,
    ):
        self.scuole = scuole
        self.total = total
        self.limit = limit
        self.offset = offset
        self.filter_search = filter_search
        self.filter_tipo = filter_tipo
        self.filter_citta = filter_citta
        self.filter_provincia = filter_provincia
        self.filter_indirizzo = filter_indirizzo
        self.sort_by = sort_by
        self.order = order

        schools_data = {
            "scuole": self.scuole,
            "total": self.total,
            "limit": self.limit,
            "offset": self.offset,
            "filter_search": self.filter_search,
            "filter_tipo": self.filter_tipo,
            "filter_citta": self.filter_citta,
            "filter_provincia": self.filter_provincia,
            "filter_indirizzo": self.filter_indirizzo,
            "sort_by": self.sort_by,
            "order": self.order,
        }

        super().__init__(status_code, schools_data)
