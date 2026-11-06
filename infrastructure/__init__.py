from infrastructure.helpdesk import HelpdeskSDK, helpdesk_store, reset_helpdesk

reset_helpdesk()

helpdesk_sdk = HelpdeskSDK()

__all__ = [
    "helpdesk_sdk",
    "helpdesk_store",
    "reset_helpdesk",
]
