from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.enums import EstadoOrganizacion
from models.organizacion import Organizacion
from schemas.organizacion_schema import OrganizacionCreate, OrganizacionUpdate


ORGANIZACION_DEMO_NOMBRE = "Organización Demo"
ORGANIZACION_DEMO_SLUG = "organizacion-demo"
ORGANIZACION_DEMO_EMAIL = "demo@example.com"


def _normalizar_slug(slug: str) -> str:
    return slug.strip().lower()


def _buscar_organizacion_por_slug(db: Session, slug: str) -> Organizacion | None:
    return db.query(Organizacion).filter(Organizacion.slug == _normalizar_slug(slug)).first()


def obtener_o_crear_organizacion_demo(db: Session) -> Organizacion:
    """Garantiza una organizacion base para desarrollo y datos heredados."""
    organizacion = _buscar_organizacion_por_slug(db, ORGANIZACION_DEMO_SLUG)
    if organizacion:
        if organizacion.email_contacto != ORGANIZACION_DEMO_EMAIL:
            # Mantiene seeds existentes alineados con el dominio demo actual.
            organizacion.email_contacto = ORGANIZACION_DEMO_EMAIL
            db.add(organizacion)
        return organizacion

    organizacion = Organizacion(
        nombre=ORGANIZACION_DEMO_NOMBRE,
        slug=ORGANIZACION_DEMO_SLUG,
        email_contacto=ORGANIZACION_DEMO_EMAIL,
        estado=EstadoOrganizacion.activa,
    )
    db.add(organizacion)
    db.flush()
    return organizacion


def crear_organizacion(datos: OrganizacionCreate, db: Session) -> Organizacion:
    slug = _normalizar_slug(datos.slug)
    if _buscar_organizacion_por_slug(db, slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una organizacion con ese slug.",
        )

    organizacion = Organizacion(
        nombre=datos.nombre.strip(),
        slug=slug,
        email_contacto=str(datos.email_contacto).strip().lower(),
        estado=datos.estado,
    )
    db.add(organizacion)
    db.commit()
    db.refresh(organizacion)
    return organizacion


def obtener_organizacion_por_id(organizacion_id: UUID, db: Session) -> Organizacion:
    organizacion = db.get(Organizacion, organizacion_id)
    if not organizacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organizacion no encontrada.",
        )
    return organizacion


def obtener_organizacion_por_slug(slug: str, db: Session) -> Organizacion:
    organizacion = _buscar_organizacion_por_slug(db, slug)
    if not organizacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organizacion no encontrada.",
        )
    return organizacion


def listar_organizaciones(db: Session, skip: int = 0, limit: int = 100) -> list[Organizacion]:
    return (
        db.query(Organizacion)
        .order_by(Organizacion.fecha_creacion.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def actualizar_organizacion(
    organizacion_id: UUID,
    datos: OrganizacionUpdate,
    db: Session,
) -> Organizacion:
    organizacion = obtener_organizacion_por_id(organizacion_id, db)
    cambios = datos.model_dump(exclude_unset=True)

    if "slug" in cambios and cambios["slug"] is not None:
        nuevo_slug = _normalizar_slug(cambios["slug"])
        existente = _buscar_organizacion_por_slug(db, nuevo_slug)
        if existente and existente.id != organizacion.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una organizacion con ese slug.",
            )
        organizacion.slug = nuevo_slug

    if "nombre" in cambios and cambios["nombre"] is not None:
        organizacion.nombre = cambios["nombre"].strip()
    if "email_contacto" in cambios and cambios["email_contacto"] is not None:
        organizacion.email_contacto = str(cambios["email_contacto"]).strip().lower()
    if "estado" in cambios and cambios["estado"] is not None:
        organizacion.estado = cambios["estado"]

    db.add(organizacion)
    db.commit()
    db.refresh(organizacion)
    return organizacion


def cambiar_estado_organizacion(
    organizacion_id: UUID,
    estado: EstadoOrganizacion,
    db: Session,
) -> Organizacion:
    organizacion = obtener_organizacion_por_id(organizacion_id, db)
    organizacion.estado = estado
    db.add(organizacion)
    db.commit()
    db.refresh(organizacion)
    return organizacion
