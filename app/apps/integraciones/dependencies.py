from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.apps.integraciones.models import APIKey
from app.apps.integraciones.services import validar_api_key, verificar_scope
from app.apps.organizaciones.models import Organizacion
from app.core.database import get_db


@dataclass(frozen=True)
class APIKeyContext:
    organizacion: Organizacion
    api_key: APIKey
    scopes: set[str]


def require_api_key_scope(scope: str):
    def _dependency(
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
        db: Session = Depends(get_db),
    ) -> APIKeyContext:
        if x_api_key is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API Key requerida.")
        api_key = validar_api_key(x_api_key, db)
        verificar_scope(api_key, scope)
        organizacion = db.get(Organizacion, api_key.organizacion_id)
        if organizacion is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organizacion inactiva.")
        return APIKeyContext(
            organizacion=organizacion,
            api_key=api_key,
            scopes=set(api_key.scopes or []),
        )

    return _dependency
