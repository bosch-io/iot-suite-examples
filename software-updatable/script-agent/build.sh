#!/bin/sh

tag_version="latest"

docker image build -t lua-agent:$tag_version .
