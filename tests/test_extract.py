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


@pytest.mark.parametrize(
    ("contents", "duplicates"),
    [
        ("order_id,price,price\n1,100,200\n", "price"),
        ("order_id,price,price\n", "price"),
        (
            "product,price,product,price,price\nLaptop,100,Mouse,200,300\n",
            "price, product",
        ),
    ],
)
def test_extract_data_rejects_duplicate_headers(tmp_path, contents, duplicates):
    csv_path = tmp_path / "sales.csv"
    csv_path.write_text(contents, encoding="utf-8")

    with pytest.raises(ValueError) as error:
        extract_data(csv_path)

    assert str(error.value) == (
        f"Input file {csv_path} contains duplicate CSV headers: {duplicates}"
    )
