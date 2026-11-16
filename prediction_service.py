"""Định nghĩa câu hỏi và suy luận mô hình Q24 cho giao diện khảo sát.

Chỉ tải joblib tạo bởi chính train_predictor.py; không nhận tệp model từ client.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from train_predictor import FEATURES, VALID_CODES, COUNTRY_FILES

MODEL_DIR = Path(__file__).resolve().parent / 'models'

ATTACK_TIMES = [
    '0 lần', '1 lần', '2 hoặc 3 lần', '4 hoặc 5 lần', '6 hoặc 7 lần',
    '8 hoặc 9 lần', '10 hoặc 11 lần', '12 lần trở lên',
]
BULLIED_DAYS = ['0 ngày', '1 hoặc 2 ngày', '3 đến 5 ngày', '6 đến 9 ngày',
                '10 đến 19 ngày', '20 đến 29 ngày', 'Suốt 30 ngày']
BULLY_TYPES = [
    'Không bị bắt nạt', 'Bị đá, đẩy hoặc xô đẩy', 'Bị chế giễu về chủng tộc',
    'Bị chế giễu về tôn giáo', 'Bị chế giễu về chuyện tình dục',
    'Bị loại khỏi hoạt động chung', 'Bị chế giễu về ngoại hình',
    'Hình thức khác',
]
FREQUENCIES = ['Không bao giờ', 'Hiếm khi', 'Thỉnh thoảng',
               'Hầu hết thời gian', 'Luôn luôn']


def question(code: str, text: str, group: str, labels: list[str]) -> dict:
    values = VALID_CODES[code]
    if len(values) != len(labels):
        raise ValueError(f'Sai số phương án {code}')
    return {'id': code, 'text': text, 'group': group,
            'options': [{'value': value, 'label': label} for value, label in zip(values, labels)]}


QUESTIONS = [
    question('Q1', 'Bạn thuộc nhóm tuổi nào?', 'Thông tin chung',
             ['11 tuổi trở xuống', '12 tuổi', '13 tuổi', '14 tuổi',
              '15 tuổi', '16 tuổi', '17 tuổi', '18 tuổi trở lên']),
    question('Q2', 'Giới tính của bạn?', 'Thông tin chung', ['Nam', 'Nữ']),
    question('Q15', 'Trong 12 tháng qua, bạn bị tấn công thể chất bao nhiêu lần?',
             'Trải nghiệm trong năm qua', ATTACK_TIMES),
    question('Q16', 'Trong 12 tháng qua, bạn tham gia ẩu đả bao nhiêu lần?',
             'Trải nghiệm trong năm qua', ATTACK_TIMES),
    question('Q17', 'Trong 12 tháng qua, bạn bị thương nghiêm trọng bao nhiêu lần?',
             'Trải nghiệm trong năm qua', ATTACK_TIMES),
    question('Q20', 'Trong 30 ngày qua, bạn bị bắt nạt bao nhiêu ngày?',
             'Trải nghiệm trong năm qua', BULLIED_DAYS),
    question('Q21', 'Trong 30 ngày qua, hình thức bắt nạt thường gặp nhất là gì?',
             'Trải nghiệm trong năm qua', BULLY_TYPES),
    question('Q22', 'Trong 12 tháng qua, bạn cảm thấy cô đơn bao nhiêu lần?',
             'Cảm xúc & kết nối', FREQUENCIES),
    question('Q23', 'Trong 12 tháng qua, bạn lo lắng đến mức không ngủ được bao nhiêu lần?',
             'Cảm xúc & kết nối', FREQUENCIES),
    question('Q27', 'Bạn có bao nhiêu người bạn thân?',
             'Cảm xúc & kết nối', ['0 người', '1 người', '2 người', '3 người trở lên']),
]
assert [q['id'] for q in QUESTIONS] == FEATURES


@lru_cache(maxsize=1)
def metadata() -> dict:
    path = MODEL_DIR / 'metadata.json'
    if not path.is_file():
        raise FileNotFoundError('Chưa có mô hình. Chạy python train_predictor.py trước.')
    return json.loads(path.read_text(encoding='utf-8'))


@lru_cache(maxsize=3)
def get_model(country: str):
    info = metadata()['country_models'][country]
    # Chỉ dùng đường dẫn cục bộ cố định được tạo trong quá trình huấn luyện.
    filename = f'q24_{country.lower()}_randomforest.joblib'
    if info['model_file'] != filename:
        raise ValueError('Metadata mô hình không khớp')
    model = joblib.load(MODEL_DIR / filename)
    return model


def validate_answers(answers: dict) -> dict[str, int]:
    if not isinstance(answers, dict):
        raise ValueError('Câu trả lời phải ở dạng đối tượng JSON.')
    missing = sorted(set(FEATURES) - set(answers))
    extra = sorted(set(answers) - set(FEATURES))
    if missing or extra:
        raise ValueError(f'Cần điền đúng 10 câu. Thiếu: {missing or "không"}; không thuộc danh sách: {extra or "không"}.')
    for code in FEATURES:
        if type(answers[code]) is not int or answers[code] not in VALID_CODES[code]:
            raise ValueError(f'{code} không hợp lệ. Chỉ chấp nhận mã trả lời thuộc quy ước khảo sát.')
    # Không chấp nhận câu trả lời mâu thuẫn Q20=0 ngày, Q21 bị bắt nạt.
    if (answers['Q20'] == 1) != (answers['Q21'] == 1):
        raise ValueError('Q20 và Q21 không nhất quán: không bị bắt nạt phải chọn Q21 = Không bị bắt nạt.')
    return {code: answers[code] for code in FEATURES}


def infer(country: str, answers: dict[str, int]) -> dict:
    if country not in COUNTRY_FILES:
        raise ValueError('Chọn quốc gia Bhutan, Morocco hoặc UAE.')
    normalized = validate_answers(answers)
    X = pd.DataFrame([normalized], columns=FEATURES).astype(float)
    model = get_model(country)
    index_yes = list(model.classes_).index(1)
    yes_score = float(model.predict_proba(X)[0, index_yes])
    code = 1 if yes_score >= 0.5 else 2
    info = metadata()['country_models'][country]
    return {
        'country': country, 'target': 'Q24',
        'predicted_code': code,
        'predicted_label': 'Có' if code == 1 else 'Không',
        'model_score_yes': round(yes_score, 4),
        'threshold': 0.5,
        'model_name': info['algorithm'],
        'metrics': info['metrics'], 'test_rows': info['test_rows'],
        'training_rows': info['train_rows'],
        'caution': ('Dự đoán thống kê từ khảo sát GSHS 2016, không phản ánh chính xác '
                    'suy nghĩ của một người và không dùng để chẩn đoán hoặc kết luận an toàn.'),
    }
