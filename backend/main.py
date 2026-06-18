from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(
    title="Fayan backend",
    description="提供法眼的后端服务",
    version="1.0.0",
)

ALLOWED_ORIGINS = [
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    # allow_orgins = ALLOWED_ORIGINS,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """
    根路径健康检查接口
    """
    return {"message": "backend start success"}

from api.v1 import contracts
app.include_router( contracts.router, prefix="/api/v1",tags=["合同审查"] )