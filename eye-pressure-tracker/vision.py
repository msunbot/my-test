import base64
import os

import anthropic

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")

READING_TOOL = {
    "name": "record_eye_pressure_reading",
    "description": "Record the eye pressure reading extracted from the photo.",
    "input_schema": {
        "type": "object",
        "properties": {
            "date": {
                "type": ["string", "null"],
                "description": "Date shown on the device display, formatted YYYY-MM-DD. Null if no date is visible in the photo.",
            },
            "time": {
                "type": ["string", "null"],
                "description": "Time shown on the device display, formatted HH:MM in 24-hour time. Null if no time is visible in the photo.",
            },
            "pressure_left": {
                "type": ["number", "null"],
                "description": "Left eye pressure reading in mmHg, if visible/labeled L or LEFT. Null if not present in this photo.",
            },
            "pressure_right": {
                "type": ["number", "null"],
                "description": "Right eye pressure reading in mmHg, if visible/labeled R or RIGHT. Null if not present in this photo.",
            },
        },
        "required": ["date", "time", "pressure_left", "pressure_right"],
    },
}

PROMPT = (
    "This is a photo of a home eye-pressure (tonometer) device display, taken by an "
    "elderly user tracking their spouse's eye pressure readings. Read the digits shown "
    "on the device screen carefully.\n\n"
    "- If the device shows a date and/or time on its screen, extract those.\n"
    "- If the device shows readings labeled for left/right eye (e.g. 'L' / 'R', or two "
    "separate numbers), extract each into the matching field.\n"
    "- If only a single unlabeled number is shown, and you cannot tell which eye it is "
    "for, put it in pressure_right and leave pressure_left null (the user will correct "
    "this if wrong).\n"
    "- Do not guess values that are not legible - use null instead.\n\n"
    "Call the record_eye_pressure_reading tool with what you can read."
)


def extract_reading(image_bytes: bytes, media_type: str) -> dict:
    client = anthropic.Anthropic()
    b64_image = base64.standard_b64encode(image_bytes).decode("utf-8")

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=[READING_TOOL],
        tool_choice={"type": "tool", "name": "record_eye_pressure_reading"},
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64_image,
                        },
                    },
                    {"type": "text", "text": PROMPT},
                ],
            }
        ],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "record_eye_pressure_reading":
            return block.input

    return {"date": None, "time": None, "pressure_left": None, "pressure_right": None}
