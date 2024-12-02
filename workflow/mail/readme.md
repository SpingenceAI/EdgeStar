# Mail Interface

### 1. Mail provider setup

Follow the gmail_setup to create the token.json file and put it in the mail_interface folder.

1. [Gmail Setup](docs/gmail/setup.md)

   - after setup steps, make sure `token.json` file is in the mail_interface folder (`mail_interface/token.json`).

2. [Microsoft Graph Setup](docs/microsoft_graph/setup.md)
   - after setup steps, make sure set the `TENANT_ID`, `CLIENT_ID`, `SECRET`, `OFFICE_USER_ID`,`BOT_MAIL_FOLDER_ID` were set in the environment variables file(`.env.mail.example`).

### 2. Set Provider

Set the `MAIL_PROVIDER` in the environment variables file(`.env.example`) to `gmail` or `graph`.

### 3. Check Ollama and stt server alive

check ollama service:

```
curl http://localhost:15703
```

check stt service:

```
curl http://localhost:15706
```

If any of the above servers are not alive, follow the Readme of the service folder to start the server.

[Service Readme](../../services/readme.md)

### 4. Start the mail interface server

```
docker compose -f mail_interface-docker-compose.yml --env-file envs/.env.example up
```

### 5. Test the mail interface

Send the email with title which follow the "Mail Router" format.
The email will be routed to the respective service based on the title.

### Mail Router format:

- [ASK-CHATBOT] => Chatbot
- [TOOL-CHATBOT] => Chatbot
- [TOOL-DS] => Data Summarizer
- [TOOL-WS] => Web Search
