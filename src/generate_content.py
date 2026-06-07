import os
from groq import Groq

_client = None


def get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client


def select_best_idea(ideas):
    """Use Groq to pick the most LinkedIn-worthy idea from the list."""
    if not ideas:
        raise ValueError("No ideas provided")
    if len(ideas) == 1:
        return ideas[0]

    numbered = "\n".join(f"{i+1}. {idea['title']}" for i, idea in enumerate(ideas))
    response = get_client().chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a LinkedIn content strategist for an AI/ML engineer. "
                    "Pick the topic that will get the most engagement from recruiters, "
                    "developers, and business owners. Reply with ONLY the number."
                ),
            },
            {
                "role": "user",
                "content": f"Today's topics:\n{numbered}\n\nBest topic number?",
            },
        ],
        max_tokens=5,
        temperature=0.3,
    )
    try:
        idx = int(response.choices[0].message.content.strip()) - 1
        return ideas[idx] if 0 <= idx < len(ideas) else ideas[0]
    except Exception:
        return ideas[0]


def generate_linkedin_post(idea) -> tuple[str, str]:
    """
    Generate a LinkedIn post body and hashtags using Groq.
    Returns (content, hashtags) as separate strings.
    - content  → pure post text, no hashtags
    - hashtags → space-separated tags like '#AI #MachineLearning #DataScience'
    """
    # --- Post body (no hashtags) ---
    body_response = get_client().chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """You are an AI/ML engineer sharing your genuine thoughts on LinkedIn.

Rules you MUST follow:
- Write like a human, not a chatbot. No "In today's rapidly evolving landscape" nonsense.
- Start strong — drop the reader into a real insight or observation immediately.
- Medium length: 150-250 words. Not a tweet, not an essay.
- Use line breaks between paragraphs for readability (LinkedIn formatting).
- Do NOT include hashtags — those will be added separately.
- Do NOT include any intro like "Here's a post:" — output ONLY the post text.
- Do NOT use fluffy closings like "What do you think? Drop a comment below!"
- Sound like someone who actually works in AI/ML and has real opinions.""",
            },
            {
                "role": "user",
                "content": (
                    f"Write a LinkedIn post about this topic:\n"
                    f"Title: {idea['title']}\n"
                    f"Context: {idea.get('summary', 'No additional context')}"
                ),
            },
        ],
        max_tokens=550,
        temperature=0.85,
    )
    content = body_response.choices[0].message.content.strip()

    # --- Hashtags (separate call for clean output) ---
    tag_response = get_client().chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "Generate 5-6 LinkedIn hashtags for this AI/ML post topic. "
                    "Mix broad tags (#AI, #MachineLearning) with specific ones (#LLM, #DataScience). "
                    "Recruiters and tech professionals must actively search these tags. "
                    "Output ONLY the hashtags on one line, space-separated. No explanation."
                ),
            },
            {
                "role": "user",
                "content": f"Topic: {idea['title']}",
            },
        ],
        max_tokens=60,
        temperature=0.4,
    )
    hashtags = tag_response.choices[0].message.content.strip()

    return content, hashtags


def generate_image_prompt(idea):
    """Generate a Pollinations.ai image prompt for the topic."""
    response = get_client().chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "Generate a short, vivid image prompt for an AI image generator. "
                    "The image must be: professional, tech-themed, suitable for LinkedIn, "
                    "no text or letters in the image. "
                    "Return ONLY the prompt, nothing else. Max 20 words."
                ),
            },
            {
                "role": "user",
                "content": f"Topic: {idea['title']}",
            },
        ],
        max_tokens=60,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()
