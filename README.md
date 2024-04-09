# Newsletter Automation for New Letters

This script fetches emails from a Gmail inbox, summarizes their content using OpenAI's API, and sends a summary email.

## Steps:

1. Import necessary libraries and modules.
2. Load environment variables from a `.env` file.
3. Set up authentication scopes and API keys.
4. Define constants for email fetching and summarization.
5. Create a function to get the Gmail service.
6. Create a function to extract text from email parts.
7. Create functions to clean and sanitize the extracted text.
8. Create a function to fetch and parse emails from the Gmail inbox.
9. Create a function to summarize text using OpenAI's API.
10. Create a function to summarize the content of fetched emails.
11. Create a function to send an email using the Gmail service.
12. Create a function to create an email MIME message object.
13. Create a function to generate an HTML email template with summaries.
14. Update the main script execution to fetch emails, summarize their content, generate an HTML summary, and send the summary email.


## To Run in `venv`
```
python -m src.email_fetcher
```

## Troubleshooting
Currently have an issue where the Gmail auth expires after about 7 days. Haven't prioritized working around it. Wrote a quick script to easily update it.

1. `python -m src.reauthorize_google_oauth`
  - Accept OAuth
2. Add the Base64-encoded string (copied to clipboard) to repo's [GitHub Actions secrets](https://github.com/afurth89/newsletter_for_my_newsletters/settings/secrets/actions) --> `TOKEN_PICKLE_BASE64`
