# Deployment Notes

## Chosen deployment target

The cloud-ready target for this project is **Streamlit Community Cloud**.

Why this target was chosen:

- the repo now includes a dedicated Streamlit entrypoint: `streamlit_app.py`
- Streamlit is a direct fit for a Python-only interactive app
- it keeps the project aligned with the single current implementation in this repository
- it is simple enough for this assignment without extra hosting complexity

## Files added for deployment

- `streamlit_app.py`
- `.streamlit/config.toml`
- `requirements.txt` updated with `streamlit`, `beautifulsoup4`, and `pandas`

## What is deployed vs. what is prepared

This workspace is **not a Git repository**, and I do **not** have access to your GitHub or Streamlit Cloud account from this environment. Because of that, the project is prepared for deployment, but I could not complete the final publish step to a live public URL from here.

## Publish steps

Based on the current Streamlit Community Cloud docs:

1. Put this project in a GitHub repository.
2. Ensure the repo includes `requirements.txt` and `streamlit_app.py`.
3. In Streamlit Community Cloud, click `Create app`.
4. Select the repository, branch, and the entrypoint file `streamlit_app.py`.
5. Deploy the app and wait for the build to finish.

Official docs used:

- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://docs.streamlit.io/deploy/streamlit-community-cloud

## Recommended repository checklist before publishing

- commit `streamlit_app.py`
- commit `.streamlit/config.toml`
- commit the updated `requirements.txt`
- keep `oscar_task2.sqlite3` in the repo if you want the cloud app to start without rebuilding
- otherwise, add a build/start flow that recreates the database from `full_data.csv`

## Runtime note

The app performs live Wikipedia requests. Streamlit Community Cloud supports outbound network access, so the Wikipedia enrichment should work there as long as the dependency install succeeds and Wikipedia does not rate-limit the app.
