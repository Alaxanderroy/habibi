from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
import httpx
import os
import time

app = FastAPI()

# ===========================
# CONFIG
# ===========================

CUSTOMER_API_KEY = os.getenv("CUSTOMER_API_KEY", "STEVE")
ROOTX_API_KEY = os.getenv("ROOTX_API_KEY", "Premium_CypherX")

RATE_LIMIT_SECONDS = 0

ip_last_request = {}

# ===========================
# RATE LIMIT
# ===========================

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
                "message": "Too many requests"
            }
        )

    ip_last_request[ip] = now

    return await call_next(request)

# ==========================================================
# VEHICLE DETAILS API
# ==========================================================

@app.get("/")
async def vehicle_details(
    key: str = Query(None),
    reg_number: str = Query(None)
):

    if key != CUSTOMER_API_KEY:
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "message": "Invalid API Key"
            }
        )

    if not reg_number:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "reg_number is required"
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

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": str(e)
            }
        )

# ==========================================================
# VEHICLE -> MOBILE API
# ==========================================================

@app.get("/mobile")
async def vehicle_mobile(
    key: str = Query(None),
    vehicle_number: str = Query(None)
):

    if key != CUSTOMER_API_KEY:
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "message": "Invalid API Key"
            }
        )

    if not vehicle_number:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "vehicle_number is required"
            }
        )

    target_url = (
        "https://rootx-osint.in/"
        f"?type=v_num"
        f"&key={ROOTX_API_KEY}"
        f"&query={vehicle_number}"
    )

    try:

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(target_url)

        data = response.json()

        # Response Format 1
        if "data" in data:

            return {
                "success": data.get("success", True),
                "vehicle_number": data["data"].get("vehicle_number"),
                "mobile_number": data["data"].get("mobile_number"),
                "cached": data.get("cached", False),
                "response_time": data.get("response_time")
            }

        # Response Format 2
        if "vehicle" in data:

            return {
                "success": data.get("success", True),
                "vehicle_number": data.get("vehicle"),
                "mobile_number": data.get("mobile"),
                "cached": data.get("cached", False),
                "response_time": data.get("response_time")
            }

        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message": "No data found",
                "response": data
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
