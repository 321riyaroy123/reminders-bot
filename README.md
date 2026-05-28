# 💖 Google Calendar → Telegram Notification Agent

A cute, motivational Python agent that watches your Google Calendar and sends you adorable Telegram reminders before every event. Deployable as a background worker on **Render** in minutes!

---

## ✨ What it does

| When | What you get |
|---|---|
| Every morning at 8 AM | A daily digest of all your events |
| 30 min before an event | A cute motivational reminder |
| 10 min before an event | A "heads-up!" nudge |
| Right as it starts | An energetic "GO GO GO!" message |

Example messages:
> Hey girly! 💖
> Time to do the task: **Team Standup**
> You got thissssssss!! 🌟

> SHOWTIME!! 🎬✨
> **Design Review** is live!
> Give it everything you've got — I believe in you 💕🌙

---

## 🛠️ Setup

### Step 1 — Create a Telegram Bot

1. Open Telegram, search for **@BotFather**
2. Send `/newbot` and follow the prompts → copy your **Bot Token**
3. Start a chat with your new bot
4. Get your **Chat ID** by visiting:
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   Look for `"chat": {"id": 123456789}` in the response

### Step 2 — Set up Google Calendar API

#### Option A — Service Account (recommended for Render)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → enable **Google Calendar API**
3. Go to **IAM & Admin → Service Accounts** → Create a service account
4. Create a JSON key and download it
5. Open your Google Calendar → Settings → share the calendar with the service account email (`something@project.iam.gserviceaccount.com`) with **"See all event details"** permission

#### Option B — OAuth (easier for local testing)

1. Same steps 1-2 above
2. Go to **APIs & Services → Credentials** → Create OAuth 2.0 Client ID (Desktop App)
3. Download as `credentials.json` and place it in the project folder
4. Set `AUTH_MODE=oauth` in `.env`
5. Run once locally — a browser window will open to authorise → a `token.pickle` is saved

### Step 3 — Configure environment variables

```bash
cp .env.example .env
# Edit .env with your values
```

For the service account JSON on one line:
```bash
cat service-account.json | tr -d '\n'   # paste the output into .env
# OR base64 encode it:
base64 -i service-account.json | tr -d '\n'
```

### Step 4 — Run locally

```bash
pip install -r requirements.txt
python main.py
```

---

## 🚀 Deploy to Render

1. Push this folder to a **GitHub repository**
2. Go to [render.com](https://render.com) → New → **Blueprint** → connect your repo
   - Render will auto-detect `render.yaml` and create a **Background Worker**
3. In the Render dashboard → your service → **Environment** tab, add:
   | Key | Value |
   |---|---|
   | `TELEGRAM_BOT_TOKEN` | your bot token |
   | `TELEGRAM_CHAT_ID` | your chat id |
   | `GOOGLE_SERVICE_ACCOUNT_JSON` | full JSON string (one line) |
4. Click **Deploy** 🎉

> 💡 **Tip:** The free Render tier spins down workers after inactivity. Use the **Starter** plan ($7/mo) for always-on background workers.

---

## ⚙️ Configuration

All settings can be tweaked via environment variables:

| Variable | Default | Description |
|---|---|---|
| `POLL_INTERVAL_SECONDS` | `60` | How often to check the calendar |
| `REMINDER_MINUTES_AHEAD` | `30` | First reminder (minutes before event) |
| `CLOSE_REMINDER_MINUTES` | `10` | Second reminder (minutes before event) |
| `MORNING_DIGEST_HOUR` | `8` | Hour for daily digest (0-23) |
| `CALENDAR_ID` | `primary` | Calendar to watch (`primary` or a calendar email) |

---

## 📁 Project structure

```
gcal-telegram-agent/
├── main.py              # Agent loop & orchestration
├── calendar_service.py  # Google Calendar API integration
├── telegram_service.py  # Telegram Bot API calls
├── messages.py          # Cute motivational message templates
├── requirements.txt
├── render.yaml          # Render deployment config
└── .env.example         # Environment variable template
```

---

## 🌸 Adding your own messages

Open `messages.py` and add entries to `REMINDER_MESSAGES`, `STARTING_NOW_MESSAGES`, or `MORNING_MESSAGES`. Use `{task}` for the event title and `{time}` for the start time.

```python
"You're literally a legend 🏆\n*{task}* starts at {time}!\nNo one does it like you do 🔥",
```
