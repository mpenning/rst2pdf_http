DOCHOST ?= $(shell bash -c 'read -p "documentation host: " dochost; echo $$dochost')

# Shell color codes...
#     ref -> https://stackoverflow.com/a/5947802/667301
CLR_GREEN=\033[0;32m
CLR_CYAN=\033[0;36m
CLR_YELLOW=\033[0;33m
CLR_RED=\033[0;31m
CLR_END=\033[0;0m

.DEFAULT_GOAL := build

pip:
	@echo "$(CLR_GREEN)>> Installing all python dependencies in this virtualenv.$(CLR_END)"
	pip install -Ur ./requirements.txt
.PHONY: pip

build:
	@echo "$(CLR_GREEN)>> Building the 'filesystem_webserver' Go 'go.mod' file.$(CLR_END)"
	@echo "$(CLR_CYAN)    >> Removing the old ./filesystem_webserver binary.$(CLR_END)"
	-echo "    Removing the old ./filesystem_webserver executable"
	-rm -rf ./filesystem_webserver
	@echo "$(CLR_CYAN)    >> Removing the old ./go.mod file.$(CLR_END)"
	-rm -rf ./go.mod
	@echo "$(CLR_CYAN)    >> Building a new go.mod file.$(CLR_END)"
	-echo "module command_line_demo" > ./go.mod
	-go mod tidy -v
	@echo "$(CLR_CYAN)    >> vetting...$(CLR_END)"
	cd src && go vet .
	@echo "$(CLR_CYAN)    >> compiling...$(CLR_END)"
	-cd src && go build -ldflags "-s -w" -o ../filesystem_webserver .
	# Install all python dependencies
	make pip
.PHONY: build

