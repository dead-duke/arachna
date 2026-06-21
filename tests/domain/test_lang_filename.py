from pathlib import Path

from arachna.domain.formatting.formatter import lang_for_path


def test_dockerfile():
    assert lang_for_path(Path("Dockerfile")) == "dockerfile"


def test_makefile():
    assert lang_for_path(Path("Makefile")) == "makefile"


def test_env():
    assert lang_for_path(Path(".env")) == "bash"


def test_procfile():
    assert lang_for_path(Path("Procfile")) == "yaml"


def test_unknown():
    assert lang_for_path(Path("data.bin")) == ""


def test_case_insensitive():
    assert lang_for_path(Path("DOCKERFILE")) == "dockerfile"
