import json

from oraculo_contacts.cli import run


def test_audit_json_to_stdout(tmp_path, capsys) -> None:
    source = tmp_path / "contacts.json"
    source.write_text('[{"id":"c-1","display_name":"Ada"}]', encoding="utf-8")

    exit_code = run(["audit", str(source), "--format", "json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out)["summary"]["contacts_scanned"] == 1


def test_audit_writes_json_report_without_touching_source(tmp_path, capsys) -> None:
    source = tmp_path / "contacts.json"
    destination = tmp_path / "reports" / "audit.json"
    original = "[]"
    source.write_text(original, encoding="utf-8")

    exit_code = run(["audit", str(source), "--output", str(destination)])

    assert exit_code == 0
    assert source.read_text(encoding="utf-8") == original
    assert json.loads(destination.read_text(encoding="utf-8"))["summary"]["contacts_scanned"] == 0
    assert "Contactos analizados: 0" in capsys.readouterr().out


def test_invalid_input_returns_controlled_exit_code(tmp_path, capsys) -> None:
    exit_code = run(["audit", str(tmp_path / "missing.json")])
    assert exit_code == 2
    assert "no existe" in capsys.readouterr().err


def test_refuses_output_over_source(tmp_path, capsys) -> None:
    source = tmp_path / "contacts.json"
    source.write_text("[]", encoding="utf-8")
    exit_code = run(["audit", str(source), "--output", str(source)])
    assert exit_code == 2
    assert source.read_text(encoding="utf-8") == "[]"
    assert "sobrescribir" in capsys.readouterr().err


def test_analyze_quality_json_and_preserve_source(tmp_path, capsys) -> None:
    source = tmp_path / "contacts.json"
    output = tmp_path / "quality.json"
    original = json.dumps(
        [
            {"id": "one", "display_name": "Ada", "emails": ["same@example.test"]},
            {"id": "two", "display_name": "Ada", "emails": ["same@example.test"]},
        ]
    )
    source.write_text(original, encoding="utf-8")
    exit_code = run(["analyze", str(source), "--format", "json", "--output", str(output)])
    stdout = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert stdout["summary"]["duplicate_candidates"] == 1
    assert output.is_file()
    assert source.read_text(encoding="utf-8") == original


def test_sprint_one_audit_command_remains_compatible(tmp_path, capsys) -> None:
    source = tmp_path / "contacts.json"
    source.write_text("[]", encoding="utf-8")
    assert run(["audit", str(source)]) == 0
    assert "Reporte de auditoría" in capsys.readouterr().out
