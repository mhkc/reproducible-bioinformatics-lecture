build:
	docker build . -t example-pipeline

run:
	docker run																															\
		--name=example-pipeline																								\
		-it																																		\
		--volume $(CURDIR)/volumes/temp_files:/tmp/example_pipeline						\
		--volume $(CURDIR)/volumes/data:/usr/src/example_pipeline/data				\
		example-pipeline

stop:
	docker container stop example-pipeline
	docker container rm example-pipeline
