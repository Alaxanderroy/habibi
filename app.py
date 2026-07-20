from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
import httpx
import time
import os

app = FastAPI()

# ==========================
# CONFIG
# ==========================

# Customer API Key
CUSTOMER_API_KEY = os.getenv("CUSTOMER_API_KEY", "STEVE")

# Optional Rate Limit (0 = Disabled)
RATE_LIMIT_SECONDS = 0

ip_last_request = {}

# ==========================
# Rate Limit Middleware
# ==========================

@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if RATE_LIMIT_SECONDS <= 0:
        return await call_next(request)

    ip = request.client.host
    now = time.time()

    last = ip_last_request.get(ip)

    if last and (now - last) < RATE_LIMIT_SECONDS:
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "message": "Too many requests. Please wait."
            }
        )

    ip_last_request[ip] = now
    return await call_next(request)

# ==========================
# Main API
# ==========================

@app.get("/")
async def vehicle_lookup(
    key: str = Query(None),
    reg_number: str = Query(None)
):

    # API Key Validation
    if key != CUSTOMER_API_KEY:
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "message": "Invalid API Key"
            }
        )

    # Registration Number Validation
    if not reg_number:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "reg_number parameter is required"
            }
        )

    target_url = (
        "https://web.justpolicy.in/php-vahaan/service.php/"
        f"?action=VAHAAN_DETAILS"
        f"&reg_number={reg_number}"
        "&type=rc"
    )

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(target_url)

        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )

    except httpx.TimeoutException:
        return JSONResponse(
            status_code=504,
            content={
                "success": False,
                "message": "Upstream API timeout"
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": str(e)
            }
        )
