# Newsletter for my newsletter

This script fetches emails from a Gmail inbox, summarizes their content using OpenAI's API, and sends a summary email.

## Components:
1. **Fetch and parse emails**: Uses Google OAuth to access and fetch newsletters from a designated Gmail account, and then sanitizes and parses the content into structured data ready to be summarized
2. **Summarize content with LLMs**: Each newsletter's text is fed into both [OpenAI's API](https://openai.com/index/openai-api), and an open-source `bart-large-cnn` trained with a dataset from the [HuggingFace](https://huggingface.co/)
3. **Generate and Send Summary Email**: A new email is created, containing the compiled summaries or analyses, and sent to the user's inbox. This email may include links to the full newsletters for further reading.

## Writing
I wrote about the spirit behind the project, and the process of building it. View the entire series:
- [The inspiration to build something new (and write about it)](https://andrewfurth.substack.com/p/a-newsletter-for-my-newsletters-part)
- [Charting a course for the app with my AI co-pilot](https://andrewfurth.substack.com/p/a-newsletter-for-my-newsletters-part-3b0?r=mxmyr&utm_campaign=post&utm_medium=web&triedRedirect=true)
- Get something working (coming soon)
- Can I "train" my own model to summarize? (coming soon)

## To Run in `venv`
```
python -m src.email_fetcher
```

## Troubleshooting
Currently have an issue where the Gmail auth expires after about 7 days. Haven't prioritized working around it. Wrote a quick script to easily update it.

1. `python -m src.reauthorize_google_oauth`
  - Accept OAuth
2. Add the Base64-encoded string (copied to clipboard) to repo's [GitHub Actions secrets](https://github.com/afurth89/newsletter_for_my_newsletters/settings/secrets/actions) --> `TOKEN_PICKLE_BASE64`
