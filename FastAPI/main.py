from fastapi import FastAPI
from detect_api import router as detect_router
from v8_train_api import router as train_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(detect_router)
app.include_router(train_router)

@app.get("/")
def read_root():
    return {"msg": "Alzheimer YOLOv8 API running"}
