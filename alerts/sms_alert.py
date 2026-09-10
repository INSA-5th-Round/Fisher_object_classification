import os

class SMSAlert:
    """
    Provider-neutral SMS adapter.

    This project intentionally leaves the final provider call unimplemented
    because teams may use Twilio, Africa's Talking, Safaricom, or another gateway.
    """

    def __init__(self):
        self.enabled = os.getenv("ENABLE_SMS", "false").lower() == "true"

    def send(self, message):
        if not self.enabled:
            return {"channel": "sms", "sent": False, "reason": "disabled"}

        # Replace this section with the chosen SMS provider SDK/API.
        return {
            "channel": "sms",
            "sent": False,
            "reason": "provider adapter not configured"
        }
