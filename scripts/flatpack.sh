#!/bin/bash

dir="$(readlink -m $(dirname "$0"))"
cd $dir/..

VERSION=`cat ./src/version.txt`
VERSION=${VERSION:1:10}
echo VERSION=$VERSION

# Wymaga zainstalowanych: flatpak, flatpak-builder oraz
# runtime/sdk org.freedesktop.Platform//24.08 i org.freedesktop.Sdk//24.08.

set -euo pipefail

echo ''
echo running-flatpak
echo wd:`pwd`

echo `flatpak --version` > ./src/distro.info.txt

MANIFEST="io.github.pjdude.SimpleAudioSweeper.yml"
BUILD_DIR="build-dir"
APP_ID="io.github.pjdude.SimpleAudioSweeper"
BUNDLE="${APP_ID}.flatpak"

REPO_DIR="${REPO_DIR:-repo}"

echo "== Instalacja brakującego runtime/sdk (jeśli potrzebne) =="
flatpak install -y --user flathub \
  org.freedesktop.Platform//24.08 \
  org.freedesktop.Sdk//24.08

echo ''
echo "== Budowanie =="
flatpak-builder --force-clean --user --install-deps-from=flathub "$BUILD_DIR" "$MANIFEST"

echo ''
echo "== Instalacja lokalna (do repo użytkownika) =="
flatpak-builder --user --install --force-clean "$BUILD_DIR" --repo="${REPO_DIR}" "$MANIFEST"

echo ''
echo "== bundle !! =="
flatpak build-bundle "${REPO_DIR}" "${BUNDLE}" "${APP_ID}"

#echo ''
#echo "== install !! =="
#flatpak install --user ./io.github.pjdude.SimpleAudioSweeper.flatpak

#echo ''
#echo "== run !! =="
#flatpak run io.github.pjdude.SimpleAudioSweeper
