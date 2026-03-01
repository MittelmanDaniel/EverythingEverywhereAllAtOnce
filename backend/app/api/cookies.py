from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.connection import ServiceConnection
from app.models.user import User
from app.schemas.cookies import BulkCookieSubmission, CookieSubmission
from app.utils.encryption import encrypt_cookies

router = APIRouter(prefix="/cookies", tags=["cookies"])

# Domain -> service mapping
DOMAIN_SERVICE_MAP = {
    "github.com": "github",
    "youtube.com": "youtube",
    "google.com": "youtube",  # YouTube uses Google cookies
    "goodreads.com": "goodreads",
}


def domain_to_service(domain: str) -> str | None:
    """Map a cookie domain to a known service, or None."""
    d = domain.lstrip(".")
    for key, service in DOMAIN_SERVICE_MAP.items():
        if d == key or d.endswith("." + key):
            return service
    return None


@router.post("")
async def submit_cookies(
    req: CookieSubmission,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ServiceConnection).where(
            ServiceConnection.user_id == user.id,
            ServiceConnection.service == req.service,
        )
    )
    conn = result.scalar_one_or_none()
    encrypted = encrypt_cookies([c.model_dump() for c in req.cookies])

    if conn:
        conn.cookies_encrypted = encrypted
        conn.status = "connected"
    else:
        conn = ServiceConnection(
            user_id=user.id,
            service=req.service,
            cookies_encrypted=encrypted,
            status="connected",
        )
        db.add(conn)

    await db.commit()
    return {"status": "ok", "service": req.service}


@router.post("/bulk")
async def submit_bulk_cookies(
    req: BulkCookieSubmission,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Accept ALL cookies and sort them into services by domain."""
    # Group cookies by service
    service_cookies: dict[str, list] = {}
    unmatched = 0

    for cookie in req.cookies:
        service = domain_to_service(cookie.domain)
        if service:
            service_cookies.setdefault(service, []).append(cookie.model_dump())
        else:
            # Store unmatched cookies under "other" for future use
            service_cookies.setdefault("other", []).append(cookie.model_dump())
            unmatched += 1

    # Upsert each service's cookies
    for service, cookies in service_cookies.items():
        result = await db.execute(
            select(ServiceConnection).where(
                ServiceConnection.user_id == user.id,
                ServiceConnection.service == service,
            )
        )
        conn = result.scalar_one_or_none()
        encrypted = encrypt_cookies(cookies)

        if conn:
            conn.cookies_encrypted = encrypted
            conn.status = "connected"
        else:
            conn = ServiceConnection(
                user_id=user.id,
                service=service,
                cookies_encrypted=encrypted,
                status="connected",
            )
            db.add(conn)

    await db.commit()

    services_connected = [s for s in service_cookies if s != "other"]
    return {
        "status": "ok",
        "total_cookies": len(req.cookies),
        "services_connected": services_connected,
        "unmatched_cookies": unmatched,
    }
