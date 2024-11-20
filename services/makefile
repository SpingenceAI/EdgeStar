create_network:
	sudo docker network create edgestar-network

run_services:
	docker compose -f docker-compose.yml --env-file envs/.env.example up -d
test_ollama:
	curl http://localhost:15703
test_stt:
	curl http://localhost:15706

pull_llama3.2:
	curl http://localhost:15703/api/pull -d '{"model": "llama3.2:latest"}'


stop_services:
	docker compose -f docker-compose.yml down

remove_network:
	sudo docker network rm edgestar-network