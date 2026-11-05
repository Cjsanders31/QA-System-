from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from rag import PDFStore, answer_with_context


ROOT = Path(__file__).parent
PDF_DIR = ROOT
store = PDFStore(PDF_DIR)
store.ingest()

app = FastAPI(title="Papertrail RAG")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/")
def home() -> FileResponse:
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/status")
def status() -> dict[str, int]:
    return {"documents": len({chunk.filename for chunk in store.chunks}), "chunks": len(store.chunks)}


@app.get("/api/library")
def library() -> dict[str, list[str]]:
    return {"files": sorted({chunk.filename for chunk in store.chunks})}


@app.post("/api/ingest")
async def ingest(files: list[UploadFile] = File(default=[])) -> dict[str, int]:
    for upload in files:
        if upload.filename and upload.filename.lower().endswith(".pdf"):
            (PDF_DIR / Path(upload.filename).name).write_bytes(await upload.read())
    return store.ingest()


@app.post("/api/ask")
def ask(payload: dict[str, str]) -> dict[str, object]:
    query = payload.get("query", "").strip()
    if not query:
        return {"answer": "Ask a question about your PDFs to get started.", "sources": []}
    sources = store.search(query)
    return {"answer": answer_with_context(sources), "sources": sources}
