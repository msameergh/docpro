# Docpro history

A simple diary of what was done on this project. Newest entry on top.
No passwords or keys in this file. The repo is public.

## 2026-11-04
- Problem: on the local app the sidebar (upload and Extract buttons) disappeared and could not be reopened.
- Cause: landing.py hides Streamlit's top toolbar, and the "reopen sidebar" arrow lives inside it, so it was hidden too.
- Fix: one CSS line in landing.py makes that arrow visible again. Tested: collapse the sidebar, the arrow shows, click it, sidebar returns.
- Tip: a browser refresh (F5) also brings the sidebar back.

## 2026-11-01
- Came back after about a month. The live app was broken.
- Cause: the GitHub repo had been made private, so Streamlit could not download the code ("Cloning repository... Failed").
- Fix: made the repo public again, then Reboot app on share.streamlit.io. The app worked again.
- Pushed 3 local commits to GitHub (landing page, branded app bar, CLAUDE.md notes). Live app now shows the landing page.
- Learned how it all fits: the project folder is saved with git, copied to GitHub (msameergh/docpro), and Streamlit Cloud runs the app from there. Pushing to GitHub updates the live app by itself in 1-2 minutes.
- Updated CLAUDE.md with the deployment details (not committed yet).
- Created this history file.
- To do later (optional): make the repo private again after giving Streamlit access in GitHub settings.

## 2026-10-04
- Built the app (invoices and packing lists) and deployed it to Streamlit Community Cloud.
- Added the landing page and branded app bar, and the CLAUDE.md project notes.
