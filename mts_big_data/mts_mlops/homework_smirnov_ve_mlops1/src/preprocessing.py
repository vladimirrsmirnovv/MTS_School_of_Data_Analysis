# импорты

import pandas as pd
import numpy as np
import holidays
from math import atan2, cos, radians, sin, sqrt
import category_encoders as ce

import logging

logger = logging.getLogger(__name__)
RANDOM_STATE = 42

# даты


def assign_time_of_day(hour):
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 24:
        return "evening"
    else:
        return "night"


def process_transaction_time_features(train_df, test_df):
    # Конвертация типов
    train_df['transaction_time'] = pd.to_datetime(train_df['transaction_time'])
    test_df['transaction_time'] = pd.to_datetime(test_df['transaction_time'])

    # Отдельная дата
    train_df['transaction_date'] = train_df['transaction_time'].dt.date
    test_df['transaction_date'] = test_df['transaction_time'].dt.date

    # Праздники (ВАЖНО: расширить годы, если потребуется)
    us_holidays = holidays.US(years=[2018, 2019, 2020, 2021])

    def get_holiday_name(date):
        return us_holidays.get(date) if date in us_holidays else "No Holiday"

    # Месяц, неделя, день недели, часы, минуты
    for df in [train_df, test_df]:
        df['transaction_time_month'] = df['transaction_time'].dt.month
        df['transaction_time_week'] = df['transaction_time'].dt.isocalendar().week
        df['transaction_time_day_of_the_week'] = df['transaction_time'].dt.dayofweek
        df['transaction_time_hour'] = df['transaction_time'].dt.hour
        df['transaction_time_minute'] = df['transaction_time'].dt.minute

        df["transaction_time_holidays"] = df["transaction_time"].apply(get_holiday_name)
        df['transaction_time_binning_by_part'] = df['transaction_time_hour'].apply(assign_time_of_day)

    return train_df, test_df


## расстояния

def haversine_distance(lat1, lon1, lat2, lon2, n_digits=0):
    lat1, lon1, lat2, lon2 = round(lat1, 6), round(lon1, 6), round(lat2, 6), round(lon2, 6)
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2)**2
    return round(2 * 6372800 * np.arctan2(np.sqrt(a), np.sqrt(1 - a)), n_digits)


def bearing_degree(lat1, lon1, lat2, lon2, n_digits=0):
    lat1, lon1 = np.radians(round(lat1, 6)), np.radians(round(lon1, 6))
    lat2, lon2 = np.radians(round(lat2, 6)), np.radians(round(lon2, 6))
    dlon = lon2 - lon1
    numerator = np.sin(dlon) * np.cos(lat2)
    denominator = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(dlon)
    theta = np.arctan2(numerator, denominator)
    theta_deg = (np.degrees(theta) + 360) % 360
    return round(theta_deg, n_digits)


def process_distance_features(train_df, test_df):
    # bearing_degree
    train_df['bearing_degree_1'] = bearing_degree(train_df['lat'], train_df['lon'], train_df['merchant_lat'], train_df['merchant_lon']).values
    test_df['bearing_degree_1'] = bearing_degree(test_df['lat'], test_df['lon'], test_df['merchant_lat'], test_df['merchant_lon']).values

    train_df['bearing_degree_2'] = bearing_degree(train_df['lat'], train_df['lon'], 0, 0).values
    test_df['bearing_degree_2'] = bearing_degree(test_df['lat'], test_df['lon'], 0, 0).values

    train_df['bearing_degree_3'] = bearing_degree(0, 0, train_df['merchant_lat'], train_df['merchant_lon']).values
    test_df['bearing_degree_3'] = bearing_degree(0, 0, test_df['merchant_lat'], test_df['merchant_lon']).values

    # haversine
    train_df['hav_dist_1'] = haversine_distance(train_df['lat'], train_df['lon'], train_df['merchant_lat'], train_df['merchant_lon']).values
    test_df['hav_dist_1'] = haversine_distance(test_df['lat'], test_df['lon'], test_df['merchant_lat'], test_df['merchant_lon']).values

    train_df['hav_dist_2'] = haversine_distance(train_df['lat'], train_df['lon'], 0, 0).values
    test_df['hav_dist_2'] = haversine_distance(test_df['lat'], test_df['lon'], 0, 0).values

    train_df['hav_dist_3'] = haversine_distance(0, 0, train_df['merchant_lat'], train_df['merchant_lon']).values
    test_df['hav_dist_3'] = haversine_distance(0, 0, test_df['merchant_lat'], test_df['merchant_lon']).values

    return train_df, test_df


# логарифмы, перцентили, ночные транзакции

def process_amount_and_night_features(train_df, test_df):
    # Приводим даты к строке для надежного merge (можно заменить на pd.to_datetime при необходимости)
    train_df['transaction_date'] = train_df['transaction_date'].astype(str)
    test_df['transaction_date'] = test_df['transaction_date'].astype(str)

    # Логарифм суммы
    train_df['amount_log'] = np.log1p(train_df['amount'])
    test_df['amount_log'] = np.log1p(test_df['amount'])

    # Ночные транзакции
    train_night = train_df[train_df['transaction_time_binning_by_part'] == "night"]
    test_night = test_df[test_df['transaction_time_binning_by_part'] == "night"]

    # Агрегаты по ночным транзакциям
    def night_agg(df):
        if df.empty:
            return pd.DataFrame({'transaction_date': [], 
                                 'sum_by_night_part': [], 
                                 'mean_by_night_part': [], 
                                 'median_by_night_part': []})
        return df.groupby('transaction_date')['amount'].agg(
            sum_by_night_part='sum',
            mean_by_night_part='mean',
            median_by_night_part='median'
        ).reset_index()
    
    train_night_agg = night_agg(train_night)
    test_night_agg = night_agg(test_night)

    train_df = train_df.merge(train_night_agg, on='transaction_date', how='left')
    test_df = test_df.merge(test_night_agg, on='transaction_date', how='left')

    # 90-й перцентиль по amount
    def percentile_90(df):
        if df.empty:
            return pd.DataFrame({'transaction_date': [], 'percentile_90': []})
        return df.groupby('transaction_date')['amount'].quantile(0.9).reset_index(name='percentile_90')
    
    train_90 = percentile_90(train_df)
    test_90 = percentile_90(test_df)

    train_df = train_df.merge(train_90, on='transaction_date', how='left')
    test_df = test_df.merge(test_90, on='transaction_date', how='left')

    # Защита: если колонка вдруг не появилась (мердж не сработал), создаём вручную
    if 'percentile_90' not in train_df.columns:
        train_df['percentile_90'] = -np.inf
    else:
        train_df['percentile_90'] = train_df['percentile_90'].fillna(-np.inf)
    if 'percentile_90' not in test_df.columns:
        test_df['percentile_90'] = -np.inf
    else:
        test_df['percentile_90'] = test_df['percentile_90'].fillna(-np.inf)

    # Сумма транзакций выше 90-го перцентиля
    def high_sum(df):
        if df.empty or 'percentile_90' not in df.columns:
            return pd.DataFrame({'transaction_date': [], 'sum_more_than_90': []})
        filtered = df[df['amount'] > df['percentile_90']]
        if filtered.empty:
            # Важно: если нет ни одной строки, добавим пустой датафрейм
            return pd.DataFrame({'transaction_date': df['transaction_date'].unique(), 'sum_more_than_90': [0]*len(df['transaction_date'].unique())})
        return filtered.groupby('transaction_date')['amount'].sum().reset_index(name='sum_more_than_90')
    
    train_high = high_sum(train_df)
    test_high = high_sum(test_df)

    train_df = train_df.merge(train_high, on='transaction_date', how='left')
    test_df = test_df.merge(test_high, on='transaction_date', how='left')

    # Заполняем пропуски нулями
    for col in ['sum_by_night_part', 'mean_by_night_part', 'median_by_night_part', 'sum_more_than_90']:
        if col not in train_df.columns:
            train_df[col] = 0
        else:
            train_df[col] = train_df[col].fillna(0)
        if col not in test_df.columns:
            test_df[col] = 0
        else:
            test_df[col] = test_df[col].fillna(0)

    return train_df, test_df

def process_gender_daily_stats(train_df, test_df):
    # Агрегация по полу и дате — для train
    gender_daily_stats_train = train_df.groupby(['transaction_date', 'gender']).agg(
        count=('amount', 'size'),
        mean_amount=('amount', 'mean'),
        median_amount=('amount', 'median'),
        total_sum=('amount', 'sum')
    ).reset_index()

    train_df = pd.merge(train_df, gender_daily_stats_train, on=['transaction_date', 'gender'], how='left')

    # Аналогично — для test
    gender_daily_stats_test = test_df.groupby(['transaction_date', 'gender']).agg(
        count=('amount', 'size'),
        mean_amount=('amount', 'mean'),
        median_amount=('amount', 'median'),
        total_sum=('amount', 'sum')
    ).reset_index()

    test_df = pd.merge(test_df, gender_daily_stats_test, on=['transaction_date', 'gender'], how='left')

    return train_df, test_df

# catboost encoding

def process_catboost_encoding(train_df, test_df, target_column='target'):
    train_df['ts_transaction_time'] = pd.to_datetime(train_df['transaction_time']).values.astype('int64') // 10**9
    test_df['ts_transaction_time'] = pd.to_datetime(test_df['transaction_time']).values.astype('int64') // 10**9

    cat_prep_cols = ['gender', 'jobs', 'transaction_time_holidays', 'transaction_time_binning_by_part']
    for col in cat_prep_cols:
        train_df[col] = train_df[col].astype(str)
        test_df[col] = test_df[col].astype(str)
    train_df[cat_prep_cols] = train_df[cat_prep_cols].fillna('пропуск')
    test_df[cat_prep_cols] = test_df[cat_prep_cols].fillna('пропуск')

    cat_columns = [
        'merch', 'cat_id', 'name_1', 'name_2', 'gender', 'street', 'one_city', 'us_state',
        'jobs', 'post_code', 'transaction_time_holidays', 'transaction_time_binning_by_part'
    ]
    cb_columns = [c + '_cb' for c in cat_columns]
    train_df = train_df.drop(columns=[c for c in cb_columns if c in train_df.columns], errors='ignore')
    test_df = test_df.drop(columns=[c for c in cb_columns if c in test_df.columns], errors='ignore')

    target_enc = ce.CatBoostEncoder(cols=cat_columns)
    target_enc = target_enc.fit(train_df[cat_columns], train_df[target_column])
    train_df = train_df.join(target_enc.transform(train_df[cat_columns]).add_suffix('_cb'))
    test_df = test_df.join(target_enc.transform(test_df[cat_columns]).add_suffix('_cb'))

    return train_df, test_df


def load_train_data():
    logger.info('Loading training data...')
    train = pd.read_csv("./models/train.csv")
    train['transaction_time'] = pd.to_datetime(train['transaction_time'])
    train['transaction_date'] = train['transaction_time'].dt.date

    train, _ = process_transaction_time_features(train, train.copy())
    train, _ = process_distance_features(train, train.copy())
    train, _ = process_amount_and_night_features(train, train.copy())
    train, _ = process_gender_daily_stats(train, train.copy())
    train, _ = process_catboost_encoding(train, train.copy())
    logger.info('Train data processed. Shape: %s', train.shape)
    return train


def run_preproc(train_df, test_df):
    test_df['transaction_time'] = pd.to_datetime(test_df['transaction_time'])
    test_df['transaction_date'] = test_df['transaction_time'].dt.date

    _, test_df = process_transaction_time_features(train_df.copy(), test_df)
    _, test_df = process_distance_features(train_df.copy(), test_df)
    _, test_df = process_amount_and_night_features(train_df.copy(), test_df)
    _, test_df = process_gender_daily_stats(train_df.copy(), test_df)
    _, test_df = process_catboost_encoding(train_df.copy(), test_df)
    return test_df