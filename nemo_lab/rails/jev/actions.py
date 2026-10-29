from nemoguardrails.actions import action
import jev_client

@action(name="jev_check_input")
async def jev_check_input(context: dict | None = None, **kwargs):
    return (await jev_client.classify((context or {}).get("user_message", "")))["decision"]

@action(name="jev_risk")
async def jev_risk(context: dict | None = None, **kwargs):
    return (await jev_client.classify((context or {}).get("user_message", "")))["risk"]
