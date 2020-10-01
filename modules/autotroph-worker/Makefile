# latest = 0.2.0
version=0.2.0
docker-user=jaredhanson11
name=${docker-user}/autotroph-worker

build:
	docker build . --build-arg PIP_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL} -t ${name}:${version}
push: build
	docker push ${name}:${version}
