from infrastructure import helpdesk_sdk


def main() -> None:
    """Reset the demo helpdesk store to its initial state."""

    helpdesk_sdk.reset()


if __name__ == "__main__":
    main()
