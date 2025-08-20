# FastAPI Gateway
Un gateway API basato su FastAPI che instrada le richieste a diversi microservizi e gestisce l'autenticazione e l'autenticazione jwt.
La chiave segreta è divisa in due chiavi, privata e pubblica: con la chiave privata vengono firmati i token, mentre sono verificabili tramite la controparte pubblica.
Le chiavi sono generate automaticamente e ruotate ogni 24 ore.
I refresh token, utilizzati per ottenere nuovi access token, sono utilizzabili una sola volta: quando si utilizzano viene generato un nuovo access token e un nuovo refresh token, il vecchio refresh token non è più valido e se utilizzato elimina tutte le altre sessioni dell'utente.
Gli access token sono validi per 30 minuti, i refresh token per 30 giorni, contando anche il cambio di refresh token.
## WebSocket
Il gateway supporta il routing sticky per le connessioni WebSocket, consentendo di mantenere le connessioni aperte e di instradare i messaggi tra client e microservizi alle istanze corrette.

## setup
eseguire `poetry install` per installare le dipendenze 