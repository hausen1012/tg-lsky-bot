docker 直接运行：

```sh
docker run -d \
--name tg-lsky-bot \
-e TELEGRAM_BOT_TOKEN=xxx \
-e API_BASE_URL=xxx \
-e API_USERNAME=xxx \
-e API_PASSWORD=xxx \
-e STRATEGY_ID=1 \
hausen1012/tg-lsky-bot
```

docker-compose 运行：

```yaml
version: '3'
services:
  tg-lsky-bot:
    image: hausen1012/tg-lsky-bot
    container_name: tg-lsky-bot
    restart: always
    environment:
      - BOT_TOKEN=xxx
      - API_BASE_URL=xxx
      - API_USERNAME=xxx
      - API_PASSWORD=xxx
      - STRATEGY_ID=1
```