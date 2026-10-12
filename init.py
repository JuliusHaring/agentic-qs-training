from infrastructure import customs_sdk, logistics_sdk


def main() -> None:
    """Reset the demo customs and logistics stores to their initial state."""

    customs_sdk.reset()
    logistics_sdk.reset()


if __name__ == "__main__":
    main()
