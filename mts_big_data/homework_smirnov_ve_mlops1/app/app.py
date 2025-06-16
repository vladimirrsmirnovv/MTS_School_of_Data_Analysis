import os
import sys
import pandas as pd
import logging


sys.path.append(os.path.abspath('./src'))
from preprocessing import load_train_data, run_preproc
from scorer import make_pred

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info('Starting one-shot ML scoring service (no watchdog)')
    input_file = '/app/input/test.csv'  # здесь добавляю упрощенную логику
    output_file = '/app/output/sample_submission.csv'

    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        return

    logger.info('Loading training data...')
    train = load_train_data()
    logger.info('Reading input data...')
    input_df = pd.read_csv(input_file)
    # .drop(columns=['name_1', 'name_2', 'street', 'post_code'])

    logger.info('Preprocessing...')
    processed = run_preproc(train, input_df)

    logger.info('Scoring...')
    submission = make_pred('input/test.csv')

    logger.info(f'Saving predictions to {output_file}')
    submission.to_csv(output_file, index=False)
    logger.info('Done!')

if __name__ == "__main__":
    main()