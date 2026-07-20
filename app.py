from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx
import time

app = FastAPI()

# ===== Simple In-Memory Rate Limit =====
RATE_LIMIT_SECONDS = 0
ip_last_request = {}

@app.middleware("http")
async def rate_limit(request: Request, call_next):
    ip = request.client.host
    now = time.time()

    last_time = ip_last_request.get(ip)
    if last_time and (now - last_time) < RATE_LIMIT_SECONDS:
        return JSONResponse(
            status_code=429,
            content={"error": "Ruk ja bhencho itne m kya unlimited request lega?? Paid lena h to bolo 100-400₹ @sudocypherx."}
        )

    ip_last_request[ip] = now
    return await call_next(request)

# ===== API =====
@app.get("/")
async def lookup(
    key: str = Query(None), 
    number: str = Query(None)
):
    # Fast Validation
    if key != "lundkinger3":
        return JSONResponse(status_code=403, content={"error": "Unauthorized: Invalid Key"})

    if not number:
        return JSONResponse(status_code=400, content={"error": "Number parameter is required"})

    target_url = f"https://api.subhxcosmo.in/api?key=SATYAM2&type=mobile&term={number}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(target_url, timeout=10.0)
            data = response.json()

            # Fast Filtering
            if data.get("success") and "result" in data:
                res = data["result"]
                return {
                    "results": res.get("results", []),
                    "search_time": res.get("search_time", ""),
                    "status": res.get("status", "success")
                }

            return JSONResponse(status_code=404, content={"error": "No data found"})

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": "Fast API error", "details": str(e)}
            )
