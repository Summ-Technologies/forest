# latest 0.1.0
version=latest
docker-user=jaredhanson11
name=${docker-user}/redwood

build:
	docker build . --build-arg PIP_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL} -t ${name}:${version}
push: build
	docker push ${name}:${version}
