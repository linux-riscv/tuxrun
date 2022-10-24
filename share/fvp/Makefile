LAVA_IMAGE ?= ""
RUNTIME ?= "podman"

.PHONE: build

build: fvp fvp-aemva fvp-morello

fvp: Dockerfile
	@if [ "$(LAVA_IMAGE)" = "" ]; then $(RUNTIME) build --tag tuxrun:fvp . ; else $(RUNTIME) build --build-arg image="$(LAVA_IMAGE)" --tag tuxrun:fvp . ;fi

fvp-aemva: aemva/Dockerfile
	cd aemva && $(RUNTIME) build --tag fvp:aemva-11.18.16 .

fvp-morello: morello/Dockerfile
	cd morello && $(RUNTIME) build --tag fvp:morello-0.11.33 .

clean:
	$(RUNTIME) image rm tuxrun:fvp fvp:aemva-11.18.16 fvp:morello-0.11.33
