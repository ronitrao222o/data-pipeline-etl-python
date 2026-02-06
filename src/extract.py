import csv
import logging

def extract_data(file_path):
    data = []

    try:
        with open(file_path, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
        logging.info(f"Successfully extracted data from {file_path}")

    except FileNotFoundError:
        logging.error(f"Input file not found: {file_path}")
        raise

    except Exception as e:
        logging.error(f"Error while reading file {file_path}: {e}")
        raise

    return data
