"""MindScope Q24 — ứng dụng khảo sát và dự đoán phản hồi GSHS 2016.

Chỉ chạy máy cá nhân (127.0.0.1). Không lưu câu trả lời trừ khi người dùng
đánh dấu đồng ý. Kết quả chỉ dành cho nghiên cứu thống kê, không dùng lâm sàng.
"""
from __future__ import annotations

from pathlib import Path
import base64
import hashlib
import re
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, Field, StrictInt

from prediction_service import QUESTIONS, infer, metadata
from response_store import RETENTION_DAYS, delete_response, retrieve_response, save_response

BASE_DIR = Path(__file__).resolve().parent

HTML_DOCUMENT = (BASE_DIR / 'templates' / 'index.html').read_text(encoding='utf-8')

def _embedded_hash(element_id: str, tag: str) -> str:
    match = re.search(rf'<{tag} id="{element_id}">(.*?)</{tag}>', HTML_DOCUMENT, re.DOTALL)
    if match is None:
        raise RuntimeError(f'Giao diện thiếu {element_id}: hãy chạy CAP_NHAT_GIAO_DIEN.py')
    return base64.b64encode(hashlib.sha256(match.group(1).encode('utf-8')).digest()).decode('ascii')

STYLE_HASH = _embedded_hash('mindscope-style', 'style')
SCRIPT_HASH = _embedded_hash('mindscope-script', 'script')

app = FastAPI(title='MindScope — Nghiên cứu Q24 / GSHS 2016', version='2.0.0')
app.mount('/static', StaticFiles(directory=BASE_DIR / 'static'), name='static')
templates = Jinja2Templates(directory=BASE_DIR / 'templates')


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    country: Literal['Bhutan', 'Morocco', 'UAE']
    answers: dict[str, StrictInt]
    save_response: bool = False


class ReceiptRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    receipt: str = Field(min_length=30, max_length=128, pattern=r'^[A-Za-z0-9_-]+$')


@app.middleware('http')
async def privacy_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.update({
        'Cache-Control': 'no-store',
        'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'no-referrer',
        'X-Frame-Options': 'DENY',
        'Content-Security-Policy': ("default-src 'self'; script-src 'self' 'sha256-"+SCRIPT_HASH+"'; "
                                  "style-src 'self' 'sha256-"+STYLE_HASH+"'; img-src 'self' data:; "
                                  "connect-src 'self'; object-src 'none'; base-uri 'self'; "
                                  "form-action 'self'; frame-ancestors 'none'"),
    })
    return response


@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, 'index.html')


@app.get('/api/questions')
def get_questions():
    info = metadata()
    return {
        'target': 'Q24',
        'target_question': 'Trong 12 tháng qua, bạn có bao giờ nghiêm túc nghĩ đến việc tự tử không?',
        'countries': list(info['country_models']),
        'questions': QUESTIONS,
        'training_year': 2016,
        'model': 'Random Forest',
        'retention_days': RETENTION_DAYS,
        'note': 'Nghiên cứu phản hồi khảo sát, không đánh giá sức khỏe tâm thần cá nhân.',
    }


@app.get('/api/model-info')
def model_info(country: Literal['Bhutan', 'Morocco', 'UAE']):
    item = metadata()['country_models'][country]
    return {
        'country': country,
        'algorithm': item['algorithm'],
        'train_rows': item['train_rows'],
        'test_rows': item['test_rows'],
        'metrics': item['metrics'],
    }


@app.post('/api/predict')
def predict(payload: PredictionRequest):
    try:
        result = infer(payload.country, payload.answers)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (FileNotFoundError, ImportError) as exc:
        raise HTTPException(status_code=503, detail=f'Mô hình không khả dụng: {exc}') from exc

    # Chỉ tạo và ghi DB nếu người dùng chủ động chọn lưu.
    result['saved'] = False
    if payload.save_response:
        try:
            result['receipt'] = save_response(payload.country, payload.answers, result)
        except Exception as exc:
            # Không lặng lẽ báo lưu thành công nếu ghi đĩa thất bại.
            raise HTTPException(status_code=503, detail='Không thể lưu kết quả vào SQLite. Kiểm tra quyền ghi thư mục database/.') from exc
        result['saved'] = True
    return result


@app.post('/api/records/lookup')
def lookup(payload: ReceiptRequest):
    item = retrieve_response(payload.receipt)
    if item is None:
        raise HTTPException(status_code=404, detail='Không tìm thấy biên nhận hoặc đã hết hạn.')
    return item


@app.post('/api/records/delete')
def delete(payload: ReceiptRequest):
    if not delete_response(payload.receipt):
        raise HTTPException(status_code=404, detail='Không tìm thấy biên nhận hoặc đã được xóa.')
    return {'deleted': True}


@app.get('/api/health')
def health():
    info = metadata()
    return {'status': 'ok', 'models': list(info['country_models']), 'target': 'Q24', 'version': app.version}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=5055, reload=False, access_log=False)
