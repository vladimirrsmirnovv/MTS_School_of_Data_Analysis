import pandas as pd
import logging
from catboost import CatBoostClassifier
from preprocessing import load_train_data, run_preproc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info('Importing pretrained model...')
model = CatBoostClassifier()
model.load_model('./models/my_catboost.cbm')
model_th = 0.28
logger.info('Pretrained model imported successfully...')


def make_pred(processed_df: pd.DataFrame, model_features: list, source_info="kafka_stream") -> pd.DataFrame:
    logger.info(f'Running predictions for source: {source_info}')

    missing_cols = [col for col in model_features if col not in processed_df.columns]
    if missing_cols:
        logger.warning(f"Missing columns in input data: {missing_cols}")
        for col in missing_cols:
            processed_df[col] = 0

    X = processed_df[model_features]
    y_proba = model.predict_proba(X)[:, 1]
    y_pred = (y_proba > model_th).astype(int)

    submission = pd.DataFrame({
        'score': y_proba,
        'fraud_flag': y_pred
    })

    return submission


if __name__ == '__main__':
    logger.info('Running local test inference...')
    train_df, encoder, model_features = load_train_data()
    test_df = pd.read_csv("train_data/train.csv")
    test_df_processed = run_preproc(train_df, test_df, encoder, model_features)
    submission = make_pred(test_df_processed, model_features, source_info="local")
    submission.to_csv('/app/output/sample_submission.csv', index=False)
    logger.info('sample_submission.csv saved.')