RUNTIME ?= "podman"

.PHONE: build

build: fvp fvp-morello

fvp: docker Dockerfile
	$(RUNTIME) build --tag tuxrun:fvp .

fvp-morello: morello/Dockerfile
	cd morello && $(RUNTIME) build --tag fvp:morello-0.11.19 .
