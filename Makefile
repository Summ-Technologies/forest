images-dir=./modules
images=$(shell ls ${images-dir})
libs-dir=./lib
# Exclude setup.py as a lib
libs=$(shell ls ${libs-dir} | grep -v "setup.py")

build-images:
	$(foreach image, ${images}, $(MAKE) -C ${images-dir}/${image} build || exit 1;)
push-images:
	$(foreach image, ${images}, $(MAKE) -C ${images-dir}/${image} push || exit 1;)
build-libs:
	$(foreach lib, ${libs}, /scripts/python/python-build.sh ${libs-dir}/${lib} || exit 1;)
push-libs:
	$(foreach lib, ${libs}, /scripts/python/python-push.sh ${libs-dir}/${lib} || exit 1;)