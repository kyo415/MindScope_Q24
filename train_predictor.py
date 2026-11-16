"""Huấn luyện lại 3 mô hình dự đoán phản hồi Q24 từ 10 câu khảo sát khác.

Chạy: python train_predictor.py
Dùng cho nghiên cứu/phương pháp học máy, KHÔNG phải công cụ đánh giá nguy cơ cá nhân.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
MODEL_DIR = BASE_DIR / 'models'
COUNTRY_FILES = {
    'Bhutan': '2016BTN (National).csv',
    'Morocco': '2016MAR (National).csv',
    'UAE': 'ARE2016 (National).csv',
}
# Đây là 10 biến đầu vào trong notebook gốc; tuyệt đối KHÔNG lấy Q24, Q25, Q26.
FEATURES = ['Q1', 'Q2', 'Q15', 'Q16', 'Q17', 'Q20', 'Q21', 'Q22', 'Q23', 'Q27']
VALID_CODES = {
    'Q1': tuple(range(1, 9)), 'Q2': (1, 2),
    'Q15': tuple(range(1, 9)), 'Q16': tuple(range(1, 9)),
    'Q17': tuple(range(1, 9)), 'Q20': tuple(range(1, 8)),
    'Q21': tuple(range(1, 9)), 'Q22': tuple(range(1, 6)),
    'Q23': tuple(range(1, 6)), 'Q27': tuple(range(1, 5)),
}


def load_labeled_data(path: Path) -> tuple[pd.DataFrame, pd.Series, dict]:
    frame = pd.read_csv(path, usecols=[*FEATURES, 'Q24'], low_memory=False)
    for field in [*FEATURES, 'Q24']:
        frame[field] = pd.to_numeric(frame[field], errors='coerce')
    total = len(frame)
    frame = frame[frame['Q24'].isin([1, 2])].copy()
    for field, codes in VALID_CODES.items():
        frame.loc[~frame[field].isin(codes), field] = np.nan
    # Q24 1 = Có, Q24 2 = Không
    y = (frame['Q24'] == 1).astype(int)
    return frame[FEATURES], y, {
        'total_rows': total, 'labeled_rows': len(frame),
        'missing_target_rows': total - len(frame),
        'positive_rows': int(y.sum()), 'negative_rows': int((1 - y).sum())
    }


def build_model() -> Pipeline:
    # One-hot: loại khảo sát Q21 là danh mục, KHÔNG được coi số lớn là nghiêm trọng hơn.
    prep = ColumnTransformer(transformers=[
        ('categories', Pipeline([
            ('missing', SimpleImputer(strategy='constant', fill_value=-1)),
            ('onehot', OneHotEncoder(handle_unknown='ignore')),
        ]), FEATURES)
    ], remainder='drop')
    estimator = RandomForestClassifier(
        n_estimators=240,
        max_depth=12,
        min_samples_leaf=5,
        min_samples_split=10,
        class_weight='balanced_subsample',
        n_jobs=-1,
        random_state=42,
    )
    return Pipeline([('preprocessor', prep), ('classifier', estimator)])


def main() -> None:
    MODEL_DIR.mkdir(exist_ok=True)
    report: dict = {
        'description': 'Dự đoán Q24 = 1 (Có) từ 10 câu hỏi khác; nghiên cứu minh họa, không dùng cho cá nhân.',
        'feature_columns': FEATURES,
        'target': 'Q24',
        'target_mapping': {'1': 'Có', '2': 'Không'},
        'trained_at_utc': datetime.now(timezone.utc).isoformat(),
        'sklearn_version': sklearn.__version__,
        'test_size': 0.2,
        'random_state': 42,
        'country_models': {},
    }
    for country, filename in COUNTRY_FILES.items():
        X, y, population = load_labeled_data(DATA_DIR / filename)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=42, stratify=y
        )
        pipeline = build_model()
        # Các bộ điền thiếu, mã hóa chỉ fit trên training set, không rò rỉ test.
        pipeline.fit(X_train, y_train)
        pred = pipeline.predict(X_test)
        prob = pipeline.predict_proba(X_test)[:, list(pipeline.classes_).index(1)]
        metrics = {
            'accuracy': round(float(accuracy_score(y_test, pred)), 4),
            'precision': round(float(precision_score(y_test, pred, zero_division=0)), 4),
            'recall': round(float(recall_score(y_test, pred, zero_division=0)), 4),
            'f1': round(float(f1_score(y_test, pred, zero_division=0)), 4),
            'roc_auc': round(float(roc_auc_score(y_test, prob)), 4),
        }
        model_name = f'q24_{country.lower()}_randomforest.joblib'
        joblib.dump(pipeline, MODEL_DIR / model_name, compress=3)
        report['country_models'][country] = {
            'algorithm': 'Random Forest (balanced_subsample)',
            'model_file': model_name,
            'train_rows': len(X_train),
            'test_rows': len(X_test),
            'test_positive_rows': int(y_test.sum()),
            'metrics': metrics,
            **population,
        }
        print(f'{country:9} | train={len(X_train):5}, test={len(X_test):4} | '
              f'F1={metrics["f1"]:.3f} | Recall={metrics["recall"]:.3f} | AUC={metrics["roc_auc"]:.3f}')
    (MODEL_DIR / 'metadata.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\nĐã lưu 3 mô hình tại {MODEL_DIR}')


if __name__ == '__main__':
    main()
