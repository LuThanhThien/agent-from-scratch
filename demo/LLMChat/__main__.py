def main(argv=None):
    try:
        from .app import LLMDemoApp, parse_arguments
    except ModuleNotFoundError as error:
        if error.name != "gi":
            raise
        raise SystemExit(
            "GTK Python bindings are missing. See the README app setup."
        ) from error

    args = parse_arguments(argv)
    app = LLMDemoApp(args)
    try:
        return app.run([])
    finally:
        app.shutdown()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
