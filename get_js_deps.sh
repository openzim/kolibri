#!/bin/sh

###
# download JS dependencies and place them in our templates/assets folder
# then launch our ogv.js script to fix dynamic loading links
###

if ! command -v curl > /dev/null; then
	echo "you need curl."
	exit 1
fi

if ! command -v unzip > /dev/null; then
	echo "you need unzip."
	exit 1
fi

# Absolute path this script is in.
SCRIPT_PATH="$( cd "$(dirname "$0")" ; pwd -P )"
ASSETS_PATH="${SCRIPT_PATH}/kolibri2zim/templates/assets"

echo "About to download JS assets to ${ASSETS_PATH}"

echo "getting pdf.js"
curl -L -O https://github.com/mozilla/pdf.js/releases/download/v2.6.347/pdfjs-2.6.347-es5-dist.zip
rm -rf $ASSETS_PATH/pdfjs
mkdir -p $ASSETS_PATH/pdfjs
unzip -o -d $ASSETS_PATH/pdfjs pdfjs-2.6.347-es5-dist.zip
rm -rf $ASSETS_PATH/pdfjs/web/compressed.tracemonkey-pldi-09.pdf $ASSETS_PATH/pdfjs/build/*.map $ASSETS_PATH/pdfjs/web/cmaps $ASSETS_PATH/pdfjs/web/debugger.js $ASSETS_PATH/pdfjs/web/*.map $ASSETS_PATH/pdfjs/LICENSE
rm pdfjs-2.6.347-es5-dist.zip

echo "epub.js"
curl -L -o $ASSETS_PATH/epub.min.js https://github.com/futurepress/epub.js/releases/download/v0.3.88/epub.min.js

echo "jszip.js"
curl -L -O https://github.com/Stuk/jszip/archive/v3.5.0.zip
rm -f $ASSETS_PATH/jszip.min.js
unzip -o v3.5.0.zip
mv jszip-3.5.0/dist/jszip.min.js $ASSETS_PATH/jszip.min.js
rm -rf jszip-3.5.0
rm -rf v3.5.0.zip

echo "getting video.js"
curl -L -O https://github.com/videojs/video.js/releases/download/v7.8.1/video-js-7.8.1.zip
rm -rf $ASSETS_PATH/videojs
mkdir -p $ASSETS_PATH/videojs
unzip -o -d $ASSETS_PATH/videojs video-js-7.8.1.zip
rm -rf $ASSETS_PATH/videojs/alt $ASSETS_PATH/videojs/examples
rm -f video-js-7.8.1.zip

echo "getting jquery.min.js"
curl -L -o $ASSETS_PATH/jquery.min.js https://code.jquery.com/jquery-3.5.1.min.js

echo "getting ogv.js"
curl -L -O https://github.com/brion/ogv.js/releases/download/1.6.1/ogvjs-1.6.1.zip
rm -rf $ASSETS_PATH/ogvjs
unzip -o ogvjs-1.6.1.zip
rm -f ogvjs-1.6.1/*.txt ogvjs-1.6.1/*.md
mv ogvjs-1.6.1 $ASSETS_PATH/ogvjs
rm -f ogvjs-1.6.1.zip

echo "getting videojs-ogvjs.js"
curl -L -O https://github.com/hartman/videojs-ogvjs/archive/v1.3.1.zip
rm -f $ASSETS_PATH/videojs-ogvjs.js
unzip -o v1.3.1.zip
mv videojs-ogvjs-1.3.1/dist/videojs-ogvjs.js $ASSETS_PATH/videojs-ogvjs.js
rm -rf videojs-ogvjs-1.3.1
rm -f v1.3.1.zip

echo "getting bootstrap"
curl -L -O https://github.com/twbs/bootstrap/releases/download/v5.0.0-beta2/bootstrap-5.0.0-beta2-dist.zip
rm -rf $ASSETS_PATH/bootstrap
unzip -o bootstrap-5.0.0-beta2-dist.zip
mkdir -p $ASSETS_PATH/bootstrap
mv bootstrap-5.0.0-beta2-dist/css/bootstrap.min.css bootstrap-5.0.0-beta2-dist/css/bootstrap.rtl.min.css $ASSETS_PATH/bootstrap/
mv bootstrap-5.0.0-beta2-dist/js/bootstrap.bundle.min.js bootstrap-5.0.0-beta2-dist/js/bootstrap.min.js $ASSETS_PATH/bootstrap/
rm -rf bootstrap-5.0.0-beta2-dist
rm -f bootstrap-5.0.0-beta2-dist.zip

echo "getting bootstrap icons"
curl -L -O https://github.com/twbs/icons/archive/v1.4.0.zip
rm -rf $ASSETS_PATH/bootstrap-icons
unzip -o v1.4.0.zip
rm -f icons-1.4.0/font/index.html icons-1.4.0/font/bootstrap-icons.json
mv icons-1.4.0/font $ASSETS_PATH/bootstrap-icons
rm -rf icons-1.4.0
rm -f v1.4.0.zip

echo "getting perseus renderer"
curl -L -O https://github.com/imnitishng/standalone-perseus/archive/refs/tags/v1.1.3.zip
rm -rf $ASSETS_PATH/perseus
unzip -o v1.1.3.zip
mkdir -p $ASSETS_PATH/perseus
mv standalone-perseus-1.1.3/* $ASSETS_PATH/perseus
rm -rf standalone-perseus-1.1.3/
rm -f v1.1.3.zip

if command -v fix_ogvjs_dist > /dev/null; then
    echo "fixing JS files"
    fix_ogvjs_dist $ASSETS_PATH "assets"
else
    echo "NOT fixing JS files (zimscraperlib not installed)"
fi
