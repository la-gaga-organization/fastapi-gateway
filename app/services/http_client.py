from __future__ import annotations
from enum import Enum

import httpx
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


class HttpUrl(str, Enum):
    TOKEN_SERVICE = settings.TOKEN_SERVICE_URL
    USERS_SERVICE = settings.USERS_SERVICE_URL


class HttpParams():
    """Rappresenta i parametri di una richiesta HTTP.
    Attributes:
        params (dict): Dizionario dei parametri della query.
    """

    def __init__(self):
        self.params = {}

    def __init__(self, initial_params: dict):
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


class HttpClientException(Exception):
    """Eccezione personalizzata per errori nelle richieste HTTP.
    Attributes:
        status_code (int | None): Codice di stato HTTP della risposta, se disponibile.
        server_message (str): Messaggio di errore restituito dal server.
        url (str): URL della richiesta che ha causato l'errore.
    """

    def __init__(self, message: str, server_message: str, status_code: int, url: str = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.server_message = server_message
        self.url = url


class HttpClientResponse():
    """Rappresenta la risposta di un client HTTP.
    Attributes:
        status_code (int): Codice di stato HTTP della risposta.
        data (dict | list | str | None): Dati della risposta, se presenti.
    """

    def __init__(self, status_code: int, data: dict | list | str | None = None):
        self.status_code = status_code
        self.data = data


async def send_request(url: HttpUrl, method: HttpMethod, endpoint: str, _params: HttpParams = None, _headers: HttpHeaders = None) -> HttpClientResponse:
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
            logger.error(f"HTTP request to {url} failed: {str(e)}")
            raise HttpClientException("Internal Server Error", server_message="Swiggity Swoggity, U won't find my log", url=url, status_code=500)
        except Exception as e:
            logger.error(f"Unexpected error during HTTP request to {url}: {str(e)}")
            raise HttpClientException("Internal Server Error", server_message="Swiggity Swoggity, U won't find my log", url=url, status_code=500)

        if resp.status_code >= 400:
            json = resp.json()
            if json["detail"]:
                server_message = json["detail"]
            else:
                server_message = resp.text
            raise HttpClientException(f"HTTP Error {resp.status_code}", server_message=server_message,
                                      url=url, status_code=resp.status_code)

        return HttpClientResponse(status_code=resp.status_code, data=resp.json())
