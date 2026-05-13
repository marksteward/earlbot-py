.PHONY: build run run-test shell logs

build:
	docker build -t earlbot --no-cache .

run:
	docker run -t -d --name earlbot --restart=on-failure -v $$PWD/config:/config -v $$PWD/data:/data -v $$PWD/handler:/app/handler earlbot /config/earlbot.yml

logs:
	docker logs -f earlbot --since=10m

run-test:
	docker run --rm -ti -v $$PWD/config-test:/config -v $$PWD/data:/data -v $$PWD/handler:/app/handler $$(docker build -q .) /config/earlbot-test.yml

shell:
	docker exec -ti earlbot bash
