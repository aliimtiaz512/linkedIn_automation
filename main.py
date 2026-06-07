import os
import sys

from dotenv import load_dotenv

load_dotenv()

from src.fetch_ideas import fetch_ideas
from src.generate_content import generate_image_prompt, generate_linkedin_post, select_best_idea
from src.generate_image import generate_image
from src.linkedin import post_to_linkedin
from src.sheets import log_to_sheets


def main():
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")

    print("\n=== LinkedIn Automation ===\n")

    # 1. Fetch ideas from HackerNews + RSS feeds
    print("[1/6] Fetching ideas from HackerNews + RSS feeds...")
    ideas = fetch_ideas(num_ideas=5)
    if not ideas:
        print("ERROR: No ideas found. Check internet connection or RSS feeds.")
        sys.exit(1)

    top_ideas = ideas[:3]
    print("      Top ideas found:")
    for i, idea in enumerate(top_ideas, 1):
        print(f"        {i}. {idea['title'][:80]}")

    # 2. Select best idea using Groq
    print("\n[2/6] Selecting best idea with Groq...")
    selected = select_best_idea(top_ideas)
    print(f"      Selected: {selected['title'][:80]}")

    # 3. Generate post content + hashtags (separate values)
    print("\n[3/6] Generating LinkedIn post content + hashtags...")
    content, hashtags = generate_linkedin_post(selected)
    print(f"      Content: {len(content)} chars")
    print(f"      Hashtags: {hashtags}")

    # Full post = content body + blank line + hashtags (for LinkedIn)
    full_post = f"{content}\n\n{hashtags}"

    # 4. Generate image via Pollinations.ai (free, no API key)
    print("\n[4/6] Generating image with Pollinations.ai...")
    image_path = None
    try:
        image_prompt = generate_image_prompt(selected)
        print(f"      Prompt: {image_prompt}")
        image_path = generate_image(image_prompt)
    except Exception as e:
        print(f"      WARNING: Image generation failed ({e}) — posting text only")

    # 5. Post to LinkedIn
    print("\n[5/6] Posting to LinkedIn...")
    post_id = post_to_linkedin(full_post, image_path)

    # 6. Log to Google Sheets: Content Idea | Content | Hashtags | Log timestamp
    print("\n[6/6] Logging to Google Sheets...")
    if sheet_id:
        try:
            log_to_sheets(sheet_id, selected, content, hashtags, post_id)
        except Exception as e:
            print(f"      WARNING: Sheets logging failed ({e})")
    else:
        print("      GOOGLE_SHEET_ID not set — skipping Sheets logging")

    print("\n=== Done! Post published successfully ===\n")
    print(f"Post ID  : {post_id}")
    print(f"Idea     : {selected['title']}")
    print(f"Hashtags : {hashtags}\n")


if __name__ == "__main__":
    main()
