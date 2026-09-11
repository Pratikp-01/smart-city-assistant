# UrbanEase — Smart City Assistant :
A web chatbot + API built for the **Next Gen Chatbot Arena**, Track 11 —
*Sustainable Cities & Communities*. It helps residents with sustainable
transport, waste segregation, energy/water use, green public spaces, and
civic participation.

Same three-box pattern as the StudyBuddy guide — **UI → Backend → Gemini** —
just with FastAPI instead of Streamlit, because the Arena requires a
documented external API endpoint (`POST /chat`), which Streamlit can't expose
on its own. One app serves both the browser UI and the graded API.

## What's inside

```
smart-city-assistant/
├── app.py            FastAPI backend — serves the UI and POST /chat
├── index.html         Chat UI (plain HTML/CSS/JS, no build step)
├── requirements.txt
├── .env.example        Copy to .env and add your key
├── .gitignore
├── Dockerfile          Optional, for container-based hosts
└── README.md
```

## 1. Run it locally

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Get a free key at **https://aistudio.google.com/apikey**, then:

```bash
cp .env.example .env
# edit .env and paste your key in place of paste-your-key-here
```

Run it:

```bash
uvicorn app:app --reload
```

Open **http://localhost:8000**.

## 2. The graded API

This is the exact contract from the challenge brief — no wrapper needed:

```
POST /chat
Content-Type: application/json

{ "message": "Give me five practical ways to reduce household water consumption." }
```

```json
{ "response": "..." }
```

Try it once the server is running:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"How can a household reduce electricity use?"}'
```

The web UI also sends an optional `history` array with each request so the
bot remembers the conversation — the API works fine without it, since the
brief's contract only requires `message`.

Errors (missing key, bad key, Gemini rate limits, empty message) still return
the same `{"response": "..."}` shape with a plain-language explanation, plus
an appropriate HTTP status code — so the endpoint never just crashes.

## 3. Deploy it for free

Streamlit Community Cloud (from the original guide) only hosts Streamlit
apps, so use one of these instead — all have a free tier and deploy straight
from GitHub:

**Render** (simplest)
1. Push this folder to a GitHub repo (`.env` will be excluded automatically).
2. [render.com](https://render.com) → New → Web Service → connect the repo.
3. Build command: `pip install -r requirements.txt`
   Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
4. Add an environment variable: `GEMINI_API_KEY = your-key`.
5. Deploy. You'll get a URL like `smart-city-assistant.onrender.com` — that
   same URL is both your web app and your `/chat` API endpoint.

**Hugging Face Spaces / Railway / Fly.io** — all can build the included
`Dockerfile` directly; just set the `GEMINI_API_KEY` secret/variable on
whichever platform you pick.

Either way: the key goes in the host's **environment variable / secrets**
panel, never in code, never pushed to GitHub — same rule as `.env` locally.

## 4. Make it a different track

Everything that makes this a *Smart City Assistant* instead of a generic bot
lives in one place: `SYSTEM_PROMPT` in `app.py`. It follows Role · Task ·
Context · Rules. Rewrite those four sections for any other SDG track and
redeploy — same code, different prompt.

## A heads-up on the Arena's own rules

This is a complete, working reference build so you can see and test the full
pattern end to end. The brief says work must happen inside the 180-minute
window and a project "built substantially before the event" shouldn't be
submitted — so treat this the way the guide treats StudyBuddy: study it,
run it, understand every part, then rebuild your real submission live during
the event using this as your mental template rather than uploading it as-is.
