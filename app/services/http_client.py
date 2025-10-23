from __future__ import annotations

from enum import Enum

import traceback
import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Classi e Enum per gestire richieste HTTP in modo strutturato
API_PREFIX = settings.API_PREFIX


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"

class HttpCodes(int, Enum):
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    INTERNAL_SERVER_ERROR = 500

class HttpUrl(str, Enum):
    TOKEN_SERVICE = settings.TOKEN_SERVICE_URL
    USERS_SERVICE = settings.USERS_SERVICE_URL
    SCHOOLS_SERVICE = settings.SCHOOLS_SERVICE_URL


class HttpParams():
    """Rappresenta i parametri di una richiesta HTTP.
    Attributes:
        params (dict): Dizionario dei parametri della query.
    """

    def __init__(self, initial_params: dict | None = None):
        """Inizializza i parametri della richiesta HTTP.

        Args:
            initial_params (dict | None, optional): Parametri iniziali da includere nella richiesta. Defaults to None.
        """
        if (initial_params is None):
            self.params = {}
        else:
            self.params = initial_params.copy()

    def add_param(self, key: str, value: any):
        """Aggiunge un parametro alla query della richiesta HTTP.
        Args:
            key (str): Nome del parametro.
            value (any): Valore del parametro.
        """
        self.params[key] = value

    def to_dict(self) -> dict:
        """Restituisce i parametri come dizionario.
        Returns:
            dict: Dizionario dei parametri della query.
        """
        return self.params


class HttpHeaders():
    """Rappresenta gli headers di una richiesta HTTP.
    Attributes:
        headers (dict): Dizionario degli headers HTTP.
    """

    def __init__(self, initial_headers: dict | None = None):
        self.headers = initial_headers.copy() if initial_headers else {}
        self.headers.setdefault("Content-Type", "application/json")
        self.headers.setdefault("Accept", "application/json")

    def add_header(self, key: str, value: str):
        """Aggiunge un header alla richiesta HTTP.

        Args:
            key (str): Nome dell'header.
            value (str): Valore dell'header.
        """
        self.headers[key] = value

    def to_dict(self) -> dict:
        """Restituisce gli headers come dizionario.

        Returns:
            dict: Dizionario degli headers HTTP.
        """
        return self.headers


# Errori e risposte


class OrientatiException(Exception):
    """Eccezione personalizzata generica per l'applicazione Orientati.
    Attributes:
        status_code (int | None): Codice di stato HTTP della risposta, se disponibile.
        message (str): Messaggio di errore generale.
        details (dict | None): Dettaglio del messaggio di errore.
        url (str): URL della richiesta che ha causato l'errore.
        exc (Exception | None): Eccezione originale, se presente.
    """

    def __init__(self, message: str = "Internal Server Error", status_code: int = 500, details: dict | None = None, url: str = None, exc: Exception = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details if details is not None else {"message": "Internal Server Error"}
        self.url = url
        caller_stack = "".join(traceback.format_stack()[:-1])
        logger.error("ERRORE!\n")
        logger.error(f"Stack del richiamante:\n{caller_stack}")
        if exc is not None:
            exc_tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            logger.error(f"ECCEZIONE ORIGINALE:\n{exc_tb}")

async def send_request(url: HttpUrl, method: HttpMethod, endpoint: str, _params: HttpParams = None,
                       _headers: HttpHeaders = None) -> dict:
    """Gestisce la risposta della richiesta HTTP.

    Ritorna HttpClientResponse o solleva HttpClientException in caso di errore.
    Utilizza httpx.AsyncClient per le richieste asincrone.

    Args:
        url (HttpUrl): Base URL del servizio.
        method (HttpMethod): Metodo HTTP da utilizzare.
        endpoint (str): Endpoint specifico del servizio.
        _params (HttpParams, optional): Parametri della query. Defaults to None.
        _headers (HttpHeaders, optional): Headers della richiesta. Defaults to None.

    Raises:
        HttpClientException: In caso di errore nella richiesta HTTP.
    Returns:
        HttpClientResponse: Risposta della richiesta HTTP.
    """

    url = f"{url.value}{API_PREFIX}{endpoint}"
    if not url.endswith("/") and _params is None:
        url += "/"
    async with httpx.AsyncClient(timeout=5.0) as client:
        headers = _headers.to_dict() if _headers else HttpHeaders().to_dict()
        params = _params.to_dict() if _params else {}
        try:
            match method:
                case HttpMethod.GET:
                    resp = await client.get(url, headers=headers, params=params)
                case HttpMethod.POST:
                    resp = await client.post(url, headers=headers, json=params)
                case HttpMethod.PUT:
                    resp = await client.put(url, headers=headers, json=params)
                case HttpMethod.DELETE:
                    resp = await client.delete(url, headers=headers, json=params)
                case HttpMethod.PATCH:
                    resp = await client.patch(url, headers=headers, json=params)
                case _:
                    raise ValueError(f"Unsupported HTTP method: {method}")
        except httpx.HTTPError as e:
            raise OrientatiException(exc=e, message="HTTP Error. Unable to fetch.", url=url)
        except Exception as e:
            raise OrientatiException(exc=e, url=url)

        if resp.status_code >= 400:
            json = resp.json()
            logger.info(json)

            try:
                general_message = json["message"]
            except KeyError:
                general_message = f"HTTP Error. Unable to fetch. {resp.status_code}"

            try:
                if json["detail"]:
                    server_message = json["detail"]
                else:
                    server_message = {"message":resp.text}
            except KeyError:
                server_message = {"message":resp.text}

            try:
                if json["url"]:
                    res_url = json["url"]
            except KeyError:
                res_url = url

            raise OrientatiException(message=general_message, details=server_message,
                                      url=res_url, status_code=resp.status_code)

        json_data = None
        try:
            # I microservizi riportano i dati direttamente in un {}
            json_data = resp.json()
        except Exception as e:
            raise OrientatiException(message="Invalid JSON response", url=url, exc=e)
        return json_data
