import pandas as pd
import numpy as np
import holidays
import category_encoders as ce
from math import atan2, cos, radians, sin, sqrt
import logging
from sklearn.impute import SimpleImputer

logger = logging.getLogger(__name__)
RANDOM_STATE = 42

# ПРАЗДНИКИ И ВРЕМЯ
US_HOLIDAYS = holidays.US(years=[2018, 2019, 2020, 2021])


def assign_time_of_day(hour):
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 24:
        return "evening"
    else:
        return "night"


def process_time_features(df):
    df['transaction_time'] = pd.to_datetime(df['transaction_time'])
    df['transaction_date'] = df['transaction_time'].dt.date
    df['transaction_time_month'] = df['transaction_time'].dt.month
    df['transaction_time_week'] = df['transaction_time'].dt.isocalendar().week
    df['transaction_time_day_of_the_week'] = df['transaction_time'].dt.dayofweek
    df['transaction_time_hour'] = df['transaction_time'].dt.hour
    df['transaction_time_minute'] = df['transaction_time'].dt.minute
    df['transaction_time_holidays'] = df['transaction_time'].dt.date.map(lambda x: US_HOLIDAYS.get(x, 'No Holiday'))
    df['transaction_time_binning_by_part'] = df['transaction_time_hour'].apply(assign_time_of_day)
    return df

# РАССТОЯНИЯ

def haversine_distance(lat1, lon1, lat2, lon2):
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2)**2
    return 2 * 6372800 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


def bearing_degree(lat1, lon1, lat2, lon2):
    lat1, lon1 = np.radians(lat1), np.radians(lon1)
    lat2, lon2 = np.radians(lat2), np.radians(lon2)
    dlon = lon2 - lon1
    x = np.sin(dlon) * np.cos(lat2)
    y = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(dlon)
    return (np.degrees(np.arctan2(x, y)) + 360) % 360


def process_distance_features(df):
    df['bearing_degree_1'] = bearing_degree(df['lat'], df['lon'], df['merchant_lat'], df['merchant_lon'])
    df['bearing_degree_2'] = bearing_degree(df['lat'], df['lon'], 0, 0)
    df['bearing_degree_3'] = bearing_degree(0, 0, df['merchant_lat'], df['merchant_lon'])
    df['hav_dist_1'] = haversine_distance(df['lat'], df['lon'], df['merchant_lat'], df['merchant_lon'])
    df['hav_dist_2'] = haversine_distance(df['lat'], df['lon'], 0, 0)
    df['hav_dist_3'] = haversine_distance(0, 0, df['merchant_lat'], df['merchant_lon'])
    return df

# ОБРАБОТКА ЛОГОВ, ПЕРЦЕНТИЛЕЙ, НОЧНЫХ ТРАНЗАКЦИЙ

def process_amount_features(df):
    df['amount_log'] = np.log1p(df['amount'])
    return df

# CatBoost Encoding

def process_catboost_encoding(input_df, encoder, cat_columns):
    for col in cat_columns:
        input_df[col] = input_df[col].astype(str).fillna("пропуск")
    encoded = encoder.transform(input_df[cat_columns])
    encoded.columns = [f"{col}_cb" for col in cat_columns]
    input_df = input_df.drop(columns=cat_columns)
    return pd.concat([input_df, encoded], axis=1)


# ГЛАВНАЯ ФУНКЦИЯ

def run_preproc(train_df, input_df, encoder, model_features):
    cat_columns = [
        'merch',
        'cat_id',
        'gender',
        'jobs',
        'transaction_time_holidays',
        'transaction_time_binning_by_part'
    ]
    
    input_df = process_time_features(input_df)
    input_df = process_distance_features(input_df)
    input_df = process_amount_features(input_df)
    input_df = process_catboost_encoding(input_df, encoder, cat_columns)

    if 'population_city' in input_df.columns:
        input_df['population_city'] = input_df['population_city'].fillna(train_df['population_city'].mean())

    for col in model_features:
        if col not in input_df.columns:
            input_df[col] = 0

    return input_df[model_features]

def load_train_data():
    logger.info('Loading training data...')
    train_df = pd.read_csv('fraud_detector/train_data/train.csv')

    # Временные фичи
    train_df = process_time_features(train_df)

    # Пространственные фичи
    train_df = process_distance_features(train_df)

    # Обработка суммы
    train_df = process_amount_features(train_df)

    # Категориальные признаки
    cat_columns = [
        'merch',
        'cat_id',
        'gender',
        'jobs',
        'transaction_time_holidays',
        'transaction_time_binning_by_part'
    ]

    # Преобразование типов и заполнение пропусков
    train_df[cat_columns] = train_df[cat_columns].astype(str).fillna("пропуск")

    # Обучение CatBoostEncoder
    encoder = ce.CatBoostEncoder(cols=cat_columns)
    encoder.fit(train_df[cat_columns], train_df['target'])

    # Добавление кодированных признаков
    encoded_df = encoder.transform(train_df[cat_columns]).add_suffix('_cb')
    train_df = pd.concat([train_df, encoded_df], axis=1)

    # Финальный список признаков модели
    model_features = [
        'amount_log',
        'hav_dist_1',
        'hav_dist_2',
        'hav_dist_3',
        'bearing_degree_1',
        'bearing_degree_2',
        'bearing_degree_3',
        'transaction_time_hour',
        'transaction_time_day_of_the_week',
        'transaction_time_month',
        'transaction_time_minute',
        'transaction_time_week',
        'gender_cb',
        'jobs_cb',
        'transaction_time_holidays_cb',
        'transaction_time_binning_by_part_cb',
        'merch_cb',
        'cat_id_cb'
    ]

    logger.info('Train data loaded and encoder trained. Shape: %s', train_df.shape)

    return train_df, encoder, model_features