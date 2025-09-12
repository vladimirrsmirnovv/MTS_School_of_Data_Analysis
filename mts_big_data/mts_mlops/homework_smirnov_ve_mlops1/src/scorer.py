import pandas as pd
import logging
from catboost import CatBoostClassifier
from preprocessing import load_train_data, run_preproc

from feature_imp_and_density_plot import plot_score_density_and_cdf
from feature_imp_and_density_plot import plot_feature_importance

model_features = [
    'amount', 
    'amount_log', 
    'population_city',
    'lat', 
    'lon', 
    'merchant_lat', 
    'merchant_lon', 
    'bearing_degree_1',
    'bearing_degree_2', 
    'bearing_degree_3', 
    'hav_dist_1', 
    'hav_dist_2',
    'hav_dist_3',
    'transaction_time_month', 
    'transaction_time_week',
    'transaction_time_day_of_the_week', 
    'transaction_time_hour',
    'transaction_time_minute', 
    'sum_by_night_part', 
    'mean_by_night_part', 
    'median_by_night_part',
    'percentile_90', 
    'sum_more_than_90', 
    'count', 
    'mean_amount',
    'median_amount', 
    'total_sum',
    'merch_cb', 
    'cat_id_cb', 
    'name_1_cb', 
    'name_2_cb',
    'gender_cb', 
    'street_cb', 
    'one_city_cb',
    'us_state_cb', 
    'jobs_cb',
    'post_code_cb',
    'transaction_time_holidays_cb',
    'transaction_time_binning_by_part_cb'
]

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info('Importing pretrained model...')

# Загрузка модели
model = CatBoostClassifier()
model.load_model('./models/my_catboost.cbm')

# Оптимальный порог
model_th = 0.29

logger.info('Pretrained model imported successfully...')

# Функция инференса
def make_pred(path_to_file: str) -> pd.DataFrame:
    logger.info('Reading test data from: %s', path_to_file)
    test_df = pd.read_csv(path_to_file)

    logger.info('Loading train data...')
    train_df = load_train_data()

    logger.info('Running preprocessing...')
    test_df_processed = run_preproc(train_df, test_df)

    # Оставляем только фичи из model_features и в нужном порядке
    X = test_df_processed[model_features]

    logger.info('Running predictions...')
    y_pred = (model.predict_proba(X)[:, 1] > model_th).astype(int)
    probs = model.predict_proba(X)[:, 1]

   # График плотности и ECDF
    plot_score_density_and_cdf(
        probs, 
        output_density='/app/output/pred_density.png', 
        output_cdf='/app/output/pred_cdf.png'
    )

    # График и JSON важности признаков
    plot_feature_importance(
        model, 
        model_features, 
        output_path='/app/output/top5_importance.png', 
        json_path='/app/output/top5_importances.json'
    )

    submission = pd.DataFrame({
        'index': test_df.index,
        'target': y_pred
    })
    logger.info('Prediction completed. Submission shape: %s', submission.shape)
    return submission

if __name__ == '__main__':
    submission = make_pred('/app/input/test.csv')
    submission.to_csv('/app/output/sample_submission.csv', index=False)
    logger.info('sample_submission.csv saved.')