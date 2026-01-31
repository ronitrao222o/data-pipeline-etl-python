import logging
import yaml
from extract import extract_data
from transform import transform_data
from load import load_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def load_config(path="config.yaml"):
    with open(path, "r") as file:
        return yaml.safe_load(file)

def run_pipeline():
    logging.info("ETL pipeline started")

    config = load_config()

    logging.info("Starting extract step")
    raw_data = extract_data(config["raw_data_path"])
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
