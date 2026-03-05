from io import BytesIO, TextIOWrapper

from vacancy_pipeline_py.cli.output import emit_json


def test_emit_json_handles_non_utf8_console():
    buffer = BytesIO()
    stream = TextIOWrapper(buffer, encoding="cp1252")

    emit_json({"issue": "Привет"}, stream=stream)
    stream.flush()

    assert b"\\u041f\\u0440\\u0438\\u0432\\u0435\\u0442" in buffer.getvalue()
