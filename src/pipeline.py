from extract import extract_data
from transform import transform_data
from load import load_data

RAW_DATA_PATH = "data/raw_sales_data.csv"

def run_pipeline():
    raw_data = extract_data(RAW_DATA_PATH)
    transformed_data = transform_data(raw_data)
    load_data(transformed_data)
    print("ETL Pipeline executed successfully.")

if __name__ == "__main__":
    run_pipeline()
