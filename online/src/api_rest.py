# online/src/api_rest.py
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI()

class VAResponse(BaseModel):
    ts: float
    valence: float
    arousal: float
    version: str

# in-memory last result
_last = None

@app.get("/v1/va", response_model=VAResponse)
def get_va():
    if not _last:
        return VAResponse(ts=0, valence=0.0, arousal=0.0, version="")
    return _last

def update_last(result: dict):
    global _last
    _last = VAResponse(**result)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)