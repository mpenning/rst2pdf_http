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

black:
	@echo "$(CLR_GREEN)>> Formatting with black(CLR_END)"
	black --line-length 300 rst2pdf_http.py
.PHONY: black

ruff:
	@echo "$(CLR_GREEN)>> Linting with ruff(CLR_END)"
	ENABLE_LINTERS="PYTHON_RUFF" ~/.local/bin/ruff check ./rst2pdf_http.py
.PHONY: ruff

checkmake:
	@echo "$(CLR_GREEN)>> Checking this Makefile(CLR_END)"
	# See this git repo for checkmake source...
	#    https://github.com/mrtazz/checkmake
	checkmake --config=resources/checkmake.ini ./Makefile
.PHONY: checkmake

clean:
	@echo "$(CLR_GREEN)>> cleaning the Go build cache$(CLR_END)"
	go clean -cache
.PHONY: clean

version:
	#############################################################################
	# Version number seat-belt... git_revlist_count_HEAD.txt should always match
	#   git rev-list --count HEAD
	#############################################################################
	@echo "$(CLR_CYAN)    >> Run version numbering seatbelt.$(CLR_END)"
	$(shell  git rev-list --count HEAD > resources/this_rev.tmp)
	diff -u resources/this_rev.tmp resources/git_revlist_count_HEAD.txt
	rm resources/this_rev.tmp
.PHONY: version

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
	go get github.com/gleich/logoru@v0.0.0-20230101033757-d86cd895c7a1
	go get github.com/gorilla/handlers@v1.5.1
	# pflag is buggy and doesnt handle version numbering well yet...
	go get github.com/spf13/pflag@latest
	@echo "$(CLR_CYAN)    >> go tidy$(CLR_END)"
	go mod tidy -v
	@echo "$(CLR_CYAN)    >> vetting src$(CLR_END)"
	cd src && go vet .
	@echo "$(CLR_CYAN)    >> compiling$(CLR_END)"
	#############################################################################
	# Buld the webserver binary...
	#     For reasons I'm not yet sure of, the output binary is in ./src/src
	#############################################################################
	go build -C src/ -ldflags "-s -w" .
	mv src/src ./$(WEBSERVER_BINARY_NAME)
	#############################################################################
	# Delete the local Go cache...
	#############################################################################
	$(shell chmod -R 777 $$(RST2PDFHTTPTEMPDIR))
	rm -rf $$RST2PDFHTTPTEMPDIR
	#############################################################################
	# Install all python dependencies
	#############################################################################
	make pip
	#############################################################################
	# Format with black
	#############################################################################
	make black
	#############################################################################
	# Look for dead python code...
	#############################################################################
	make vulture
	make ruff
.PHONY: all

