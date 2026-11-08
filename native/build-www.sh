#!/bin/sh
# Copies the web app into native/www so Capacitor can bundle it. Run from anywhere.
set -e
cd "$(dirname "$0")"
rm -rf www && mkdir www
for f in ../index.html ../basketball.html ../games.js ../logos.js ../fonts.css ../logo.png ../manifest.webmanifest; do cp "$f" www/; done
cp -r ../fonts ../icons ../vendor www/
# the service worker is for the website only; the app bundles its own files
echo "www ready: $(du -sh www | cut -f1)"
