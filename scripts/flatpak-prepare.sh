#!/bin/bash

dir="$(readlink -m $(dirname "$0"))"
cd $dir/..

VERSION=`cat ./src/version.txt`
VERSION=${VERSION:1:10}
echo VERSION=$VERSION

COMMIT_SHA=${GITHUB_SHA:-xxxxx}

replace() {
    local from="$1"
    local to="$2"
    sed "s/${from//\//\\/}/${to//\//\\/}/g"
}

cat io.github.pjdude.SimpleAudioSweeper.template.yml | replace COMMIT_SHA_TO_REPLACE $COMMIT_SHA | replace VERSION_TO_REPLACE $VERSION > io.github.pjdude.SimpleAudioSweeper.yml
cat io.github.pjdude.SimpleAudioSweeper.metainfo.template.xml | replace VERSION_TO_REPLACE $VERSION > io.github.pjdude.SimpleAudioSweeper.metainfo.xml
