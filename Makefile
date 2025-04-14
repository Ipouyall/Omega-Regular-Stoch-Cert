TIME_LIMIT=300

.PHONY: run verifications controls visual benchmark docker-build docker-run docker-save docker-load

benchmark: verifications controls visual

verifications:
	@for i in 0 1 2 3 4 5; do \
		make --no-print-directory run INPUT=benchmark/random_walk_verification_$$i.json; \
	done

controls:
	@for i in 0 1 2 3 4; do \
		make --no-print-directory run INPUT=benchmark/random_walk_control_$$i.json; \
	done

visual:
	@python3 -m system --input "log.jsonl" --visualize

run:
	@if [ -z "$(INPUT)" ]; then \
		echo "Usage: make run INPUT=path/to/input.json"; \
		exit 1; \
	fi; \
	if command -v timeout &> /dev/null; then \
		TIMEOUT_CMD="timeout"; \
	elif command -v gtimeout &> /dev/null; then \
		TIMEOUT_CMD="gtimeout"; \
	else \
		echo "Error: timeout or gtimeout not found. Install coreutils on macOS."; \
		exit 1; \
	fi; \
	$$TIMEOUT_CMD $(TIME_LIMIT) python3 -m system --input "$(INPUT)" --output "log.jsonl" --dump-log; \
	EXIT_CODE=$$?; \
	if [ $$EXIT_CODE -eq 124 ]; then \
		echo "Terminated: Exceeded $(TIME_LIMIT)s for $(INPUT)"; \
	elif [ $$EXIT_CODE -ne 0 ]; then \
		echo "Script failed (exit code $$EXIT_CODE) for $(INPUT)"; \
	else \
		echo "Completed: $(INPUT) within time limit."; \
	fi


docker: docker-build docker-run

docker-build:
	@docker build -t system:v0.1 .

docker-run: docker-build
	@docker run -it system:v0.1

docker-save: docker-build
	@docker save -o system.tar system:v0.1

docker-load: system.tar
	@docker load -i system.tar

system.tar: docker-save