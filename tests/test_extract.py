import pytest

from src.extract import extract_data


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig"])
def test_extract_data_preserves_headers_and_unicode_values(tmp_path, encoding):
    csv_path = tmp_path / "sales.csv"
    csv_path.write_text(
        'order_id,product\r\n1,"Caf\u00e9, premium"\r\n',
        encoding=encoding,
    )

    assert extract_data(csv_path) == [
        {"order_id": "1", "product": "Caf\u00e9, premium"}
    ]
