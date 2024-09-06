docker 直接运行：

```sh
docker run -d \
--name tg-lsky-bot \
-e TELEGRAM_BOT_TOKEN=xxx \
-e API_BASE_URL=xxx \
-e API_USERNAME=xxx \
-e API_PASSWORD=xxx \
-e STRATEGY_ID=1 \
-e ALLOWED_USERS=xxx \
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
      - ALLOWED_USERS=xxx
```


- TELEGRAM_BOT_TOKEN：机器人的 token
- API_BASE_URL：兰空图床 url，这个地址为图床的接口页面展示的 url，如：http://img.xxx.com/api/v1
- API_USERNAME：兰空图床用户名
- API_PASSWORD：兰空图床密码
- STRATEGY_ID：策略id，这个如果使用的本地存储一般为1
- ALLOWED_USERS：允许使用机器人的用户id，通过 [userinfobot](https://t.me/userinfobot) 获取，不设置则所有用户均可使用