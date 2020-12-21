# bnbot
A discord bot you can play blackjack against.

### docker-compose.yml
```
version: '3'
services:
  bnbot:
    image: "bnbn/bnbot:latest"
    environment:
      BN_TOKEN: "<TOKEN>"
      PG_DBNAME: "<NAME>"
      PG_DBUSER: "<USER>"
      PG_DBPASSWORD: "<PASSWORD>"
      PG_DBHOST: "<IP>"
      PG_DBPORT: "<PORT>"
```