import os
import sys
import pandas as pd
import logging
import json
import traceback

from confluent_kafka import Consumer, Producer

sys.path.append(os.path.abspath('./src'))

from preprocessing import load_train_data, run_preproc
from scorer import make_pred

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Переменные окружения
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TRANSACTIONS_TOPIC = os.getenv("KAFKA_TRANSACTIONS_TOPIC", "transactions")
SCORING_TOPIC = os.getenv("KAFKA_SCORING_TOPIC", "scoring")

class ProcessingService:
    def __init__(self):
        self.consumer_config = {
            'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
            'group.id': 'ml-scorer',
            'auto.offset.reset': 'earliest'
        }
        self.producer_config = {
            'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS
        }

        self.consumer = Consumer(self.consumer_config)
        self.consumer.subscribe([TRANSACTIONS_TOPIC])
        self.producer = Producer(self.producer_config)

        # Загрузка обучающего набора, энкодера и признаков модели
        self.train, self.encoder, self.model_features = load_train_data()

    def process_messages(self):
        logger.info("Started processing loop.")
        while True:
            msg = self.consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                logger.error(f"Kafka error: {msg.error()}")
                continue

            try:
                data = json.loads(msg.value().decode('utf-8'))

                # Проверка корректности данных
                if 'transaction_id' not in data or 'data' not in data:
                    raise ValueError("Message must contain 'transaction_id' and 'data' fields.")

                transaction_id = data['transaction_id']
                input_df = pd.DataFrame([data['data']])

                # Препроцессинг
                processed_df = run_preproc(
                    self.train, input_df, self.encoder, self.model_features
                )

                # Предсказание
                submission = make_pred(
                    processed_df, self.model_features, source_info="kafka_stream"
                )
                submission['transaction_id'] = transaction_id

                result = {
                    "score": float(submission["score"].iloc[0]),
                    "fraud_flag": int(submission["fraud_flag"].iloc[0]),
                    "transaction_id": transaction_id
                }

                # Отправка обратно в Kafka
                self.producer.produce(
                    SCORING_TOPIC,
                    value=json.dumps(result).encode('utf-8')
                )
                self.producer.flush()

                logger.info(f"Scored transaction {transaction_id}, score={result['score']}, fraud_flag={result['fraud_flag']}")

            except Exception as e:
                logger.error(f"Error processing message: {e}")
                logger.debug(traceback.format_exc())

if __name__ == "__main__":
    logger.info("Starting Kafka ML scoring service...")
    service = ProcessingService()
    try:
        service.process_messages()
    except KeyboardInterrupt:
        logger.info("Service stopped by user.")