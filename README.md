# Dockwatch Telegram Relay

A small Docker relay that receives **Mattermost webhook notifications from Dockwatch** and forwards them to a **Telegram group or Telegram forum topic**.

This is useful when Dockwatch does not support Telegram `message_thread_id` directly.

## How it works

```text
Dockwatch -> Mattermost webhook -> Dockwatch Telegram Relay -> Telegram
```

The relay exposes a Mattermost-compatible webhook endpoint:

```text
/hooks/dockwatch
```

Dockwatch sends notifications there, and the relay forwards them to Telegram using your bot token, chat ID and optional topic/thread ID.

## Features

- Works with Dockwatch Mattermost notifications
- Sends messages to Telegram groups
- Supports Telegram forum topics with `TELEGRAM_THREAD_ID`
- Runs as a small Docker container
- No external services required

## Environment variables

| Variable | Required | Description |
|---|---:|---|
| `TELEGRAM_BOT_TOKEN` | Yes | Telegram bot token from BotFather |
| `TELEGRAM_CHAT_ID` | Yes | Telegram group/channel chat ID, usually starting with `-100` |
| `TELEGRAM_THREAD_ID` | No | Telegram forum topic/thread ID |
| `PYTHONUNBUFFERED` | No | Recommended value: `1` |

## Docker Compose

Create a `docker-compose.yml` like this:

```yaml
services:
  dockwatch-telegram-relay:
    image: dockwatch-telegram-relay:1.0.0
    container_name: dockwatch-telegram-relay
    restart: unless-stopped
    environment:
      TELEGRAM_BOT_TOKEN: "YOUR_TELEGRAM_BOT_TOKEN"
      TELEGRAM_CHAT_ID: "-100xxxxxxxxxx"
      TELEGRAM_THREAD_ID: "YOUR-THREAD-ID"
      PYTHONUNBUFFERED: "1"
    ports:
      - "18080:8080"
```

Start it:

```bash
docker compose up -d
```

## Dockwatch setup

In Dockwatch, create a **Mattermost** notification sender.

Use:

```text
Name: Dockwatch Telegram
Webhook URL: http://YOUR_SERVER_IP:18080/hooks/dockwatch
Username: Dockwatch
```

Example:

```text
Webhook URL: http://YOUR_SERVER_IP:18080/hooks/dockwatch
```

Then send a test notification from Dockwatch.

## Test manually

You can test the relay with:

```bash
curl -X POST http://localhost:18080/hooks/dockwatch \
  -H "Content-Type: application/json" \
  -d '{"text":"Test Dockwatch Telegram Relay","username":"Dockwatch"}'
```

If everything is working, the message should appear in Telegram.

## Use the prebuilt image from GitHub Releases

Download the image archive from the release page, then load it:

```bash
gunzip -c dockwatch-telegram-relay-v1.0.0-amd64.tar.gz | docker load
```

Then use this image in Docker Compose:

```yaml
image: dockwatch-telegram-relay:1.0.0
```

## Build manually

You can also build the image yourself:

```bash
docker build -t dockwatch-telegram-relay:1.0.0 .
```

Then run it with Docker Compose using:

```yaml
image: dockwatch-telegram-relay:1.0.0
```

## Telegram notes

To send messages to a Telegram forum topic, set:

```yaml
TELEGRAM_THREAD_ID: "YOUR-THREAD-ID"
```

If you do not need a specific topic, remove the variable or leave it empty.

The Telegram bot must be added to the group and must have permission to send messages.

## Security

Never commit your real Telegram bot token to GitHub.

Use a private `docker-compose.yml`, a local `.env` file, or environment variables on your server.

If you accidentally publish your bot token, revoke it immediately from BotFather and generate a new one.

## Troubleshooting

### The container is running but Telegram returns `404 Not Found`

The Telegram bot token is probably wrong, empty, or not passed correctly to the container.

Check your environment variables.

### Telegram returns `chat not found`

The bot may not be inside the group, or the `TELEGRAM_CHAT_ID` may be wrong.

### Telegram returns `message thread not found`

The `TELEGRAM_THREAD_ID` is probably wrong, or the group is not a forum group.

### Dockwatch cannot save the webhook

Try refreshing the Dockwatch page and entering the Mattermost sender again.

Use this URL format:

```text
http://YOUR_SERVER_IP:18080/hooks/dockwatch
```

## License

MIT
