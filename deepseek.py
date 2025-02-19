

while True:
    a=input(("\n\nEnter Question: "))

    from openai import OpenAI

    client = OpenAI(
    base_url = "https://integrate.api.nvidia.com/v1",
    api_key = "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"
    )

    completion = client.chat.completions.create(
    model="meta/llama-3.3-70b-instruct",
    messages=[{"role":"user","content":a}],
    temperature=0.2,
    top_p=0.7,
    max_tokens=1024,
    stream=True
    )

   
    for chunk in completion:
        if chunk.choices[0].delta.content is not None and chunk.choices[0].delta.content != "<think>" and chunk.choices[0].delta.content != "</think>":
            print(chunk.choices[0].delta.content, end="")

