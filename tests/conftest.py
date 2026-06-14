from __future__ import annotations


def pytest_addoption(parser) -> None:  # noqa: ANN001
    parser.addoption(
        "--hardware",
        action="store_true",
        default=False,
        help="enable explicitly guarded hardware tests",
    )
