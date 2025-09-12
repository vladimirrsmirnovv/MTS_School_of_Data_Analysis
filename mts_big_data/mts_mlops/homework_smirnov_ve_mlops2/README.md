# Real-Time Fraud Detection System

**DISCLAIMER**

Данный проект выполнен в рамках домашнего задания MLOps2.

Каркас для сервиса подготовлен в демонстрационных целях для студентов курса МТС ШАД 2025 в рамках занятий по MLOps. Датасеты предоставлены в рамках соревнования https://www.kaggle.com/competitions/teta-ml-1-2025

Система для обнаружения мошеннических транзакций в реальном времени с использованием ML-модели и Kafka для потоковой обработки данных.

## 🏗️ Архитектура

Компоненты системы:

1. **`interface`** (Streamlit UI):
   
   Создан для удобной симуляции потоковых данных с транзакциями. Реальный продукт использовал бы прямой поток данных из других систем.
    - Имитирует отправку транзакций в Kafka через CSV-файлы.
    - Генерирует уникальные ID для транзакций.
    - Загружает транзакции отдельными сообщениями формата JSON в топик kafka `transactions`.

2. **`fraud_detector`** (ML Service):
   - Загружает предобученную модель CatBoost (`my_catboost.cbm`).
   - Выполняет препроцессинг данных:
     - Извлечение временных признаков
     - Гео-расстояния
     - Кодирование категориальных переменных
   - Производит скоринг с порогом 0.28.
   - Выгружает результат скоринга в топик kafka `scoring`

3. **Kafka Infrastructure**:
   - Zookeeper + Kafka брокер
   - `kafka-setup`: автоматически создает топики `transactions` и `scoring`
   - Kafka UI: веб-интерфейс для мониторинга сообщений (порт 8080)

## 🚀 Быстрый старт

### Требования
- Docker 20.10+
- Docker Compose 2.0+

### Запуск

```bash
git clone https://github.com/your-repo/fraud-detection-system.git
cd fraud-detection-system

# Сборка и запуск всех сервисов

# Запустить поочередно
docker-compose build fraud_detector
docker-compose up fraud_detector

# Либо единой командой
docker-compose up --build fraud_detector

# Важно запустить интерфейс Streamlit UI, это делается так:
docker-compose up -d interface

# Важно запустить интерфейс Apache Kafka UI, это делается так:
docker-compose up -d kafka-ui
```

После запуска:
- **Streamlit UI**: http://localhost:8501/
- **Kafka UI**: http://localhost:8080
- **Логи сервисов**: 
  ```bash
  docker-compose logs <service_name>  # Например: fraud_detector, kafka, interface

## 🛠️ Использование

### 1. Загрузка данных:

 - Загрузите CSV через интерфейс Streamlit. Для тестирования работы проекта используется файл формата `test.csv` из соревнования https://www.kaggle.com/competitions/teta-ml-1-2025
 - Пример структуры данных:
    ```csv
    transaction_time,amount,lat,lon,merchant_lat,merchant_lon,gender,...
    2023-01-01 12:30:00,150.50,40.7128,-74.0060,40.7580,-73.9855,M,...
    ```
 - Для первых тестов рекомендуется загружать небольшой семпл данных (до 100 транзакций) за раз, чтобы исполнение кода не заняло много времени.

### 2. Мониторинг:
 - **Kafka UI**: Просматривайте сообщения в топиках transactions и scoring
 - **Логи обработки**: /app/logs/service.log внутри контейнера fraud_detector

### 3. Результаты:

 - Скоринговые оценки пишутся в топик scoring в формате:
    ```json
    {
    "score": 0.995, 
    "fraud_flag": 1, 
    "transaction_id": "d6b0f7a0-8e1a-4a3c-9b2d-5c8f9d1e2f3a"
    }
    ```
## Структура проекта

Добавлена папка model.py, где можно при желании поменять логику обучения модели и переобучить её на новые данные / с новыми гиперпараметрами / с новым списком признаков.

В данном случае было необходимо изменить список признаков, на которых модель обучается, с целью упрощения процесса построения прогноза и адаптации к скорингу разовых наблюдений (часть признаков имела место быть только в контексте батчевого скоринга).

```
HOMEWORK_SMIRNOV_VE_MLOPS2

.
├── catboost_info/
│   ├── learn/
│   │   └── events.out.tfevents   # Логи обучения CatBoost (TensorBoard)
│   ├── catboost_training.json    # Конфигурация обучения CatBoost
│   ├── learn_error.tsv           # Ошибки на итерациях
│   └── time_left.tsv             # Прогноз оставшегося времени
├── fraud_detector/
│   ├── app/
│   │   └── app.py                # Основное приложение (API/сервис)
│   ├── models/
│   │   ├── model.py              # Обёртка над ML-моделью
│   │   └── my_catboost.cbm       # Сериализованная модель CatBoost
│   ├── src/
│   │   ├── preprocessing.py      # Логика препроцессинга данных
│   │   └── scorer.py             # Функции для инференса и метрик
│   ├── train_data/
│   │   └── train.csv             # Тренировочный датасет
│   ├── .gitignore                # Исключения для git
│   ├── Dockerfile                # Образ для ML-сервиса
│   └── requirements.txt          # Зависимости Python для сервиса
├── interface/
│   ├── .streamlit/
│   │   └── config.toml           # Конфигурация Streamlit
│   ├── app.py                    # UI-приложение на Streamlit
│   ├── Dockerfile                # Образ для UI
│   └── requirements.txt          # Зависимости Python для UI
├── docker-compose.yaml           # Поднятие всех сервисов (ML + UI)
└── README.md                     # Документация проекта
```

## Настройки Kafka
```yml
Топики:
- transactions (входные данные)
- scoring (результаты скоринга)

Репликация: 1 (для разработки)
Партиции: 3
```

*Примечание:* 

Для полной функциональности убедитесь, что:
1. Модель `my_catboost.cbm` размещена в `fraud_detector/models/`
2. Тренировочные данные находятся в `fraud_detector/train_data/`
3. Порты 8080, 8501 и 9095 свободны на хосте