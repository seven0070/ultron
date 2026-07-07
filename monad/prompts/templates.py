"""Bundled prompt templates."""

TEMPLATES: dict[str, str] = {
    "chat": (
        "{system}\n\n"
        "{history}\n"
        "User: {user}\n"
        "Assistant:"
    ),
    "coding": (
        "You are an expert software engineer. Provide clean, correct, well-commented code.\n\n"
        "Task:\n{user}\n\n"
        "Answer:"
    ),
    "creative": (
        "You are a creative brainstorming partner. Generate imaginative, varied ideas.\n\n"
        "Prompt:\n{user}\n\n"
        "Ideas:"
    ),
    "summarization": (
        "Summarize the following text concisely and accurately.\n\n"
        "Text:\n{user}\n\n"
        "Summary:"
    ),
    "analysis": (
        "Analyze the following thoroughly. Provide reasoning, evidence, and conclusions.\n\n"
        "Subject:\n{user}\n\n"
        "Analysis:"
    ),
}
