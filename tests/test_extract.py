import pytest

from src.extract import extract_data


@pytest.mark.parametrize(
    ("contents", "columns"),
    [
        ("order_id,,price\n1,Mouse,100\n", "2"),
        ("order_id,product,\n1,Mouse,100\n", "3"),
        ("order_id, \t,price\n1,Mouse,100\n", "2"),
        ("order_id,\n", "2"),
        (",product,\n1,Mouse,100\n", "1, 3"),
    ],
)
def test_extract_data_rejects_blank_headers(tmp_path, contents, columns):
    csv_path = tmp_path / "sales.csv"
    csv_path.write_text(contents, encoding="utf-8")

    with pytest.raises(ValueError) as error:
        extract_data(csv_path)

    assert str(error.value) == (
        f"Input file {csv_path} contains blank CSV headers at columns: {columns}"
    )


@pytest.mark.parametrize(
    ("contents", "line_number", "column_count"),
    [
        ("order_id,product\n1,Mouse,unexpected\n", 2, 3),
        ("order_id,product\n1,Mouse\n2,Keyboard,extra,values\n", 3, 4),
        ('order_id,product\n1,"Mouse\npremium",extra\n', 3, 3),
        ("order_id,product\n1,Mouse,\n", 2, 3),
    ],
)
def test_extract_data_rejects_extra_values(tmp_path, contents, line_number, column_count):
    csv_path = tmp_path / "sales.csv"
    csv_path.write_text(contents, encoding="utf-8")

    with pytest.raises(ValueError) as error:
        extract_data(csv_path)

    assert str(error.value) == (
        f"Input file {csv_path} contains extra CSV values "
        f"at line {line_number}: expected 2 columns, got {column_count}"
    )


def test_extract_data_keeps_missing_values_for_record_validation(tmp_path):
    csv_path = tmp_path / "sales.csv"
    csv_path.write_text("order_id,product\n1\n", encoding="utf-8")

    assert extract_data(csv_path) == [{"order_id": "1", "product": None}]


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
