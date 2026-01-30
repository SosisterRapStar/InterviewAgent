.PHONY: help build run run-interactive stop clean logs shell

build:
	docker compose build

run:
	docker compose run --rm interview-agent

stop:
	docker compose down

shell:
	docker exec -it interview-agent bash

clean:
	docker-compose down
