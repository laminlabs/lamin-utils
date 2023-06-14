from pathlib import Path

import nox

nox.options.default_venv_backend = "none"


@nox.session
def lint(session: nox.Session) -> None:
    session.install("pre-commit")
    session.run("pre-commit", "install")
    session.run("pre-commit", "run", "--all-files")


@nox.session
def build(session):
    session.install(".[dev,test]")
    session.run(
        "pytest",
        "-s",
        "--cov=lamin_logger",
        "--cov-append",
        "--cov-report=term-missing",
    )
    session.run("coverage", "xml")
    prefix = "." if Path("./lndocs").exists() else ".."
    session.install(f"{prefix}/lndocs")
    session.run("lndocs")
