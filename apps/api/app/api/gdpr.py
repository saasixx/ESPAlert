"""API de cumplimiento RGPD/LOPDGDD — acceso, exportación y eliminación de datos."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserZone, UserFilter
from app.models.report import CollaborativeReport
from app.api.auth import get_current_user

router = APIRouter(prefix="/me", tags=["gdpr"])


@router.get("/data")
async def export_my_data(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    RGPD Art. 15 — Derecho de acceso.
    Exporta todos los datos personales del usuario en formato JSON.
    """
    # Zones
    zones_result = await db.execute(
        select(UserZone).where(UserZone.user_id == user.id)
    )
    zones = [
        {"id": str(z.id), "label": z.label, "created_at": z.created_at.isoformat() if z.created_at else None}
        for z in zones_result.scalars().all()
    ]

    # Filters
    filters_result = await db.execute(
        select(UserFilter).where(UserFilter.user_id == user.id)
    )
    filters = [
        {"id": str(f.id), "event_types": f.event_types, "min_severity": f.min_severity}
        for f in filters_result.scalars().all()
    ]

    # Reports
    reports_result = await db.execute(
        select(CollaborativeReport).where(CollaborativeReport.user_id == user.id)
    )
    reports = [
        {
            "id": str(r.id),
            "report_type": r.report_type,
            "intensity": r.intensity,
            "lat": r.lat,
            "lon": r.lon,
            "comment": r.comment,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reports_result.scalars().all()
    ]

    return {
        "export_date": datetime.now(timezone.utc).isoformat(),
        "user": {
            "id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "quiet_start": str(user.quiet_start) if user.quiet_start else None,
            "quiet_end": str(user.quiet_end) if user.quiet_end else None,
            "predictive_alerts": user.predictive_alerts,
        },
        "zones": zones,
        "filters": filters,
        "reports": reports,
        "meta": {
            "app": "ESPAlert",
            "data_controller": "ESPAlert",
            "purpose": "Servicio de alertas de emergencia en España",
            "legal_basis": "Consentimiento del usuario (RGPD Art. 6.1.a)",
            "contact": "privacidad@espalert.es",
        },
    }


@router.delete("/account", status_code=200)
async def delete_my_account(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    RGPD Art. 17 — Derecho de supresión.
    Elimina la cuenta del usuario y todos sus datos asociados.
    """
    # Delete all user data in order (foreign keys)
    await db.execute(sa_delete(CollaborativeReport).where(CollaborativeReport.user_id == user.id))
    await db.execute(sa_delete(UserFilter).where(UserFilter.user_id == user.id))
    await db.execute(sa_delete(UserZone).where(UserZone.user_id == user.id))
    await db.delete(user)
    await db.commit()

    return {
        "status": "deleted",
        "detail": "Tu cuenta y todos tus datos han sido eliminados permanentemente.",
    }


@router.get("/privacy")
async def privacy_policy():
    """Política de Privacidad — RGPD/LOPDGDD."""
    return {
        "title": "Política de Privacidad — ESPAlert",
        "last_updated": "2026-02-24",
        "sections": [
            {
                "title": "1. Responsable del tratamiento",
                "content": (
                    "ESPAlert es responsable del tratamiento de tus datos personales. "
                    "Contacto: privacidad@espalert.es"
                ),
            },
            {
                "title": "2. Datos que recopilamos",
                "content": (
                    "• Email y nombre (registro)\n"
                    "• Zonas de interés geográfico (coordenadas)\n"
                    "• Preferencias de notificación\n"
                    "• Informes colaborativos (ubicación, tipo, intensidad)\n"
                    "• Token FCM para notificaciones push\n"
                    "NO recopilamos datos de salud, biométricos ni financieros."
                ),
            },
            {
                "title": "3. Base legal",
                "content": (
                    "Consentimiento del usuario (RGPD Art. 6.1.a) para alertas personalizadas. "
                    "Interés legítimo (Art. 6.1.f) para seguridad y protección civil."
                ),
            },
            {
                "title": "4. Finalidad",
                "content": (
                    "• Enviar alertas de emergencia relevantes para tus zonas\n"
                    "• Mostrar avisos meteorológicos, sísmicos y de tráfico\n"
                    "• Permitir comunicación vía red mesh en emergencias\n"
                    "• Mejorar el servicio mediante informes colaborativos"
                ),
            },
            {
                "title": "5. Tus derechos (RGPD/LOPDGDD)",
                "content": (
                    "• Acceso: GET /api/v1/me/data\n"
                    "• Supresión: DELETE /api/v1/me/account\n"
                    "• Rectificación: PATCH /api/v1/subscriptions/settings\n"
                    "• Portabilidad: los datos se exportan en JSON\n"
                    "• Contacto DPD: privacidad@espalert.es\n"
                    "• Reclamación ante la AEPD: www.aepd.es"
                ),
            },
            {
                "title": "6. Conservación",
                "content": (
                    "Datos de cuenta: mientras la cuenta esté activa. "
                    "Alertas históricas: 12 meses. "
                    "Informes colaborativos: 6 meses. "
                    "Tras la eliminación de cuenta, todos los datos se borran en 30 días."
                ),
            },
            {
                "title": "7. Transferencias internacionales",
                "content": (
                    "Los datos se almacenan en servidores dentro de la UE (DigitalOcean AMS). "
                    "Firebase (Google) procesa tokens de notificación bajo cláusulas contractuales tipo."
                ),
            },
            {
                "title": "8. Cookies y tracking",
                "content": "ESPAlert NO utiliza cookies de seguimiento ni analytics de terceros.",
            },
        ],
    }


@router.get("/terms")
async def terms_of_service():
    """Términos y condiciones de uso."""
    return {
        "title": "Términos de Uso — ESPAlert",
        "last_updated": "2026-02-24",
        "sections": [
            {
                "title": "1. Naturaleza del servicio",
                "content": (
                    "ESPAlert es un servicio informativo de alertas de emergencia. "
                    "NO sustituye a los canales oficiales de Protección Civil, "
                    "112, AEMET ni ES-Alert. Ante una emergencia real, "
                    "siga siempre las instrucciones de las autoridades."
                ),
            },
            {
                "title": "2. Sin garantía",
                "content": (
                    "La información se proporciona 'tal cual' sin garantía de "
                    "completitud, exactitud ni puntualidad. Las fuentes oficiales "
                    "pueden presentar retrasos o errores."
                ),
            },
            {
                "title": "3. Uso aceptable",
                "content": (
                    "Queda prohibido:\n"
                    "• Difundir alertas falsas mediante la red mesh o informes colaborativos\n"
                    "• Utilizar la API con fines de scraping masivo\n"
                    "• Modificar o redistribuir datos de fuentes oficiales sin atribución"
                ),
            },
            {
                "title": "4. Comunicaciones mesh",
                "content": (
                    "Los mensajes enviados por la red Meshtastic son públicos y "
                    "no están cifrados de extremo a extremo por defecto. "
                    "No envíe información personal sensible por este canal."
                ),
            },
        ],
    }
