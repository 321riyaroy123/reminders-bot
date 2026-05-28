# 💖 Google Calendar → Telegram Agent (Free on Render!)

Sends you cute motivational Telegram reminders before every Google Calendar event.
Runs 100% free on Render's free Web Service tier + UptimeRobot.

---

## How it stays alive for free

Render's free tier **spins down** web services after 15 min of no requests.
The fix: **UptimeRobot** (also free) pings your `/ping` endpoint every 5 minutes → keeps it awake 24/7.

---

## 🛠️ Setup — Step by Step

### Step 1 — Telegram Bot

1. Open Telegram → search **@BotFather** → send `/newbot`
2. Copy the **Bot Token** it gives you
3. Start a chat with your new bot (click Start)
4. Get your **Chat ID** — visit this URL in your browser:
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   Look for `"chat": {"id": 123456789}` — that number is your Chat ID

### Step 2 — Google Calendar API (Service Account)

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project → search for **Google Calendar API** → Enable it
3. Go to **IAM & Admin → Service Accounts** → Create service account (any name)
4. Click the account → **Keys tab** → Add Key → JSON → it downloads a file
5. Open **Google Calendar** on the web → Settings (⚙️) → your calendar → **Share with specific people**
6. Add the service account email (looks like `name@project.iam.gserviceaccount.com`)
7. Permission: **"See all event details"** → Send

### Step 3 — Deploy to Render (free)

1. Put all these files in a GitHub repo and push it

2. Go to [render.com](https://render.com) → Sign up free → **New → Web Service**

3. Connect your GitHub repo

4. Render settings:
   - **Name:** anything you like
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Instance Type:** Free ✅

5. Add Environment Variables (click "Advanced" → "Add Environment Variable"):

   | Key | Value |
   |---|---|
   | `TELEGRAM_BOT_TOKEN` | your token from BotFather |
   | `TELEGRAM_CHAT_ID` | your numeric chat ID |
   | `GOOGLE_SERVICE_ACCOUNT_JSON` | *(see below)* |

6. For `GOOGLE_SERVICE_ACCOUNT_JSON`: open the downloaded JSON key file,
   copy the **entire contents** and paste it as the value (one line is fine)

7. Click **Deploy** 🎉

### Step 4 — Keep it awake with UptimeRobot (free)

Render free tier sleeps after 15 min. UptimeRobot pings it to stay awake.

1. Sign up free at [uptimerobot.com](https://uptimerobot.com)
2. **New Monitor** → HTTP(s)
3. URL: `https://your-app-name.onrender.com/ping`
4. Monitoring Interval: **5 minutes**
5. Save — done! Your agent now runs 24/7 for free 🌟

---

## What you'll receive

| Timing | Message |
|---|---|
| Every morning at 8 AM | Daily digest of all events |
| 30 min before event | Cute motivational reminder 💖 |
| 10 min before event | "Heads-up!" nudge ⏰ |
| Right as it starts | Energetic GO-time alert 🔥 |

Example:
> Hey girly! 💖
> Time to do the task: *Team Standup*
> You got thissssssss!! 🌟

---

## Health check

Visit `https://your-app.onrender.com/` to see the agent's live status:
```json
{
  "ok": true,
  "agent": {
    "status": "running",
    "last_poll": "2024-01-15T09:30:00",
    "events_checked": 42,
    "notifications_sent": 7,
    "errors": 0
  }
}
```

---

## 📁 Files

```
├── main.py              # Flask server + agent loop (background thread)
├── calendar_service.py  # Google Calendar API
├── telegram_service.py  # Telegram Bot API
├── messages.py          # Cute message templates
├── requirements.txt
├── render.yaml
└── .env.example
```

## Adding more messages

Open `messages.py` and add to any list. Use `{task}` and `{time}` as placeholders:
```python
"You're literally a legend 🏆\n*{task}* starts at {time}!\nNo one does it like you 🔥",
```
