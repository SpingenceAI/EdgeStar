build_image:
	docker build -t edgestar/workflow .

run_playground_example:
	docker run --rm -it -v ${PWD}:/workspace --network edgestar-network --name workflow-playground edgestar/workflow python playground_cli.py --env envs/.env.example

run_ui_example:
	docker compose -f UI-docker-compose.yml --env-file envs/.env.example up
run_ui_daemon_example:
	docker compose -f UI-docker-compose.yml --env-file envs/.env.example up -d
stop_ui:
	docker compose -f UI-docker-compose.yml down