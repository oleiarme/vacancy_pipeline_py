from vacancy_pipeline_py.verification import run_verification


def main() -> None:
    if not run_verification():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
