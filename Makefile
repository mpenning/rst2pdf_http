DOCHOST ?= $(shell bash -c 'read -p "documentation host: " dochost; echo $$dochost')

WEBSERVER_BINARY_NAME = "filesystem_webserver"

# Shell color codes...
#     ref -> https://stackoverflow.com/a/5947802/667301
CLR_GREEN=\033[0;32m
CLR_CYAN=\033[0;36m
CLR_YELLOW=\033[0;33m
CLR_RED=\033[0;31m
CLR_END=\033[0;0m

.DEFAULT_GOAL := all

install-golangci-lint:
ifeq (,$(wildcard $$GOROOT/bin/golangci-lint))
	-rm $$GOROOT/bin/golangci-lint
endif
	# Install golangci-lint version 1.54.2 in $GOROOT/bin/
	curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b $$GOPATH/bin v1.54.2
	cd src && golangci-lint run
.PHONY: install-golangci-lint

pip:
	@echo "$(CLR_GREEN)>> Installing all python dependencies in this virtualenv$(CLR_END)"
	pip install -Ur ./requirements.txt
.PHONY: pip

vulture:
	@echo "$(CLR_GREEN)>> Run python vulture at 80-percent confidence$(CLR_END)"
	vulture --min-confidence 80 rst2pdf_http.py
.PHONY: vulture

ruff:
	@echo "$(CLR_GREEN)>> Linting with ruff(CLR_END)"
	ENABLE_LINTERS="PYTHON_RUFF" ~/.local/bin/ruff check ./rst2pdf_http.py
.PHONY: ruff

checkmake:
	@echo "$(CLR_GREEN)>> Checking this Makefile(CLR_END)"
	checkmake --config=resources/checkmake.ini ./Makefile
.PHONY: checkmake

clean:
	@echo "$(CLR_GREEN)>> cleaning the Go build cache$(CLR_END)"
	go clean -cache
.PHONY: clean

test:
	make checkmake
.PHONY: test

all:
	#############################################################################
	#
	# check this Makefile with https://github.com/mrtazz/checkmake/
	#
	#############################################################################
	make checkmake
	@echo "$(CLR_GREEN)>> Building the '$(WEBSERVER_BINARY_NAME)' Go 'go.mod' file.$(CLR_END)"
	@echo "$(CLR_CYAN)    >> Removing the old ./$(WEBSERVER_BINARY_NAME) binary.$(CLR_END)"
	-echo "    Removing the old ./$(WEBSERVER_BINARY_NAME) executable"
	-rm -rf $$WEBSERVER_BINARY_NAME
	#-$(shell echo "module filesystem_webserver" > go.mod)
	# add module requirements and sums
	@echo "$(CLR_CYAN)    >> Downloading Go requirements.$(CLR_END)"
	#############################################################################
	# Create a local Go cache to avoid version conflicts with
	#     previously-downloaded packages...
	#############################################################################
	@echo "$(CLR_CYAN)       >> Building temporary go cache directory.$(CLR_END)"
	RST2PDFHTTPTEMPDIR=$(shell mktemp -d)
	@echo "$(CLR_CYAN)    >> Versioned go module download$(CLR_END)"
	GOPATH=$$GOROOT/bin GOMODCACHE=$$RST2PDFHTTPTEMPDIR go get github.com/gleich/logoru@v0.0.0-20230101033757-d86cd895c7a1
	GOPATH=$$GOROOT/bin GOMODCACHE=$$RST2PDFHTTPTEMPDIR go get github.com/gorilla/handlers@v1.5.1
	# pflag is buggy and doesnt handle version numbering well yet...
	GOPATH=$$GOROOT/bin GOMODCACHE=$$RST2PDFHTTPTEMPDIR go get github.com/spf13/pflag@latest
	@echo "$(CLR_CYAN)    >> go tidy$(CLR_END)"
	GOPATH=$$GOROOT/bin GOMODCACHE=$$RST2PDFHTTPTEMPDIR go mod tidy -v
	@echo "$(CLR_CYAN)    >> vetting src$(CLR_END)"
	cd src && GOPATH=$$GOROOT/bin go vet .
	@echo "$(CLR_CYAN)    >> compiling$(CLR_END)"
	#############################################################################
	# Buld the webserver binary...
	#     For reasons I'm not yet sure of, the output binary is in ./src/src
	#############################################################################
	GOPATH=$$GOROOT/bin go build -C src/ -ldflags "-s -w" .
	mv src/src ./$(WEBSERVER_BINARY_NAME)
	#############################################################################
	# Delete the local Go cache...
	#############################################################################
	$(shell chmod -R 777 $$RST2PDFHTTPTEMPDIR)
	rm -rf $$RST2PDFHTTPTEMPDIR
	#############################################################################
	# Look for dead python code...
	#############################################################################
	make vulture
	#############################################################################
	# Install all python dependencies
	#############################################################################
	make pip
	make ruff
.PHONY: all

