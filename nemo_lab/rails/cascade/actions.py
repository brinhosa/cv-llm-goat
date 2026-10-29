from nemoguardrails.actions import action
import jev_client

@action(name="jev_check_input")
async def jev_check_input(context: dict | None = None, **kwargs):
    return (await jev_client.classify((context or {}).get("user_message", "")))["decision"]


@action(name="llm_self_check_blocked")
async def llm_self_check_blocked(llms=None, llm_task_manager=None, context=None, events=None, llm=None, config=None, **kwargs):
    # Colang v1 cannot read RailOutcome from a custom flow (action results are serialized), so return a bool.
    from nemoguardrails.library.self_check.input_check.actions import self_check_input
    out = await self_check_input(llms=llms, llm_task_manager=llm_task_manager, context=context, events=events,
                                 llm=llm, config=config)
    return bool(out.is_blocked)
