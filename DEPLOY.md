# Deploying Docpro to Streamlit Community Cloud

1. Create a **private** GitHub repository (github.com > New) and push this folder to it.
2. Go to https://share.streamlit.io, sign in with GitHub, click **Create app**.
   - Repository: your repo, Branch: `main`, Main file: `app.py`
   - Advanced settings: Python 3.12 (or 3.13)
3. In **Advanced settings > Secrets**, paste (with your own values):

       GEMINI_API_KEY = "your-new-key"
       APP_PASSWORD = "a-demo-password"

4. Click **Deploy**. Share the `*.streamlit.app` link plus the password.

## Before a demo
- Use a **new** Gemini API key with a spending cap (Google AI Studio).
- Use sample, non-confidential documents. Files are sent to Google Gemini.
- Upload the item master at the start of the demo (sidebar > Packing lists > Item master).
  Free hosting has a temporary disk, so the saved master is lost when the app restarts.
- The app sleeps after inactivity. Open the link a few minutes before the demo to wake it.

## Never commit
`.streamlit/secrets.toml`, `data/` (item master) and real documents. `.gitignore` already excludes them.
