from openai import OpenAI
from django.conf import settings


def generate_openai(
    model,
    prompt,
    system_prompt,
    temperature,
    max_tokens,
    top_p,
    frequency_penalty,
    presence_penalty,
):

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        response_format={"type": "json_object"},
    )

    return response.choices[0].message.content