import logging
from extract import extract_data
from transform import transform_data
from load import load_data

RAW_DATA_PATH = "data/raw_sales_data.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def run_pipeline():
    logging.info("ETL pipeline started")

    logging.info("Starting extract step")
    raw_data = extract_data(RAW_DATA_PATH)
    logging.info("Extract step completed")

    logging.info("Starting transform step")
    transformed_data = transform_data(raw_data)
    logging.info("Transform step completed")

    logging.info("Starting load step")
    load_data(transformed_data)
    logging.info("Load step completed")

    logging.info("ETL pipeline executed successfully")

if __name__ == "__main__":
    run_pipeline()
