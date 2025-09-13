# import pandas as pd
# import numpy as np
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import f1_score
# from catboost import CatBoostClassifier
# import joblib
# import sys
# import os

# # Абсолютный путь к каталогу
# PREPROCESSING_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))

# if PREPROCESSING_DIR not in sys.path:
#     sys.path.append(PREPROCESSING_DIR)

# from preprocessing import load_train_data, run_preproc


# # Загружаем данные
# train_df, encoder, model_features = load_train_data()

# # Разделение на train/val
# X_train, X_val, y_train, y_val = train_test_split(
#     train_df[model_features], train_df['target'], test_size=0.25,
#     random_state=42, stratify=train_df['target']
# )

# # Оптимальные параметры
# best_params = {
#     'iterations': 200,
#     'learning_rate': 0.24008436863847432,
#     'depth': 10,
#     'l2_leaf_reg': 5.064713404918217,
#     'border_count': 128
# }

# # Обучаем модель
# model_catboost = CatBoostClassifier(
#     **best_params,
#     random_state=14,
#     verbose=100
# )
# model_catboost.fit(X_train, y_train)

# # Поиск лучшего порога
# def find_best_threshold(y_true, y_scores):
#     best_threshold, best_f1 = 0, 0
#     for t in np.arange(0, 1.01, 0.01):
#         f1 = f1_score(y_true, y_scores >= t)
#         if f1 > best_f1:
#             best_f1, best_threshold = f1, t
#     return best_threshold, best_f1

# y_val_proba = model_catboost.predict_proba(X_val)[:, 1]
# best_threshold, best_f1 = find_best_threshold(y_val, y_val_proba)

# print(f"Оптимальный порог: {best_threshold}")
# print(f"F1-score на валидации: {best_f1}")

# # Сохраняем модель и энкодер
# model_catboost.save_model('fraud_detector/models/my_catboost.cbm')
# joblib.dump(encoder, 'fraud_detector/models/catboost_encoder.pkl')