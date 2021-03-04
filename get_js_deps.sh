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
mv ogvjs-1.6.1 $ASSETS_PATH/ogvjs
rm -f ogvjs-1.6.1.zip

echo "getting videojs-ogvjs.js"
curl -L -O https://github.com/hartman/videojs-ogvjs/archive/v1.3.1.zip
rm -f $ASSETS_PATH/videojs-ogvjs.js
unzip -o v1.3.1.zip
mv videojs-ogvjs-1.3.1/dist/videojs-ogvjs.js $ASSETS_PATH/videojs-ogvjs.js
rm -rf videojs-ogvjs-1.3.1
rm -f v1.3.1.zip

echo "getting material-components-web.min.js"
curl -L -O https://unpkg.com/material-components-web@latest/dist/material-components-web.min.js
rm -f $ASSETS_PATH/material-components-web.min.js
mv material-components-web.min.js $ASSETS_PATH/material-components-web.min.js

echo "getting material-components-web.min.css"
curl -L -O https://unpkg.com/material-components-web@latest/dist/material-components-web.min.css
rm -f $ASSETS_PATH/material-components-web.min.css
mv material-components-web.min.css $ASSETS_PATH/material-components-web.min.css

echo "getting roboto-mono font"
curl -L -o roboto-mono.zip http://google-webfonts-helper.herokuapp.com/api/fonts/roboto-mono?download=zip\&subsets=vietnamese,latin-ext,latin,greek,cyrillic-ext,cyrillic\&variants=100,200,300,500,600,700,regular\&formats=woff,woff2
rm -rf $ASSETS_PATH/fonts/roboto-mono
mkdir -p $ASSETS_PATH/fonts/roboto-mono
unzip -o -d $ASSETS_PATH/fonts/roboto-mono roboto-mono.zip
rm -f roboto-mono.zip

echo "getting material icons"
curl -L -o material-icons.woff2 https://fonts.gstatic.com/s/materialicons/v70/flUhRq6tzZclQEJ-Vdg-IuiaDsNc.woff2
rm -rf $ASSETS_PATH/material-icons.woff2
mv material-icons.woff2 $ASSETS_PATH/material-icons.woff2

if command -v fix_ogvjs_dist > /dev/null; then
    echo "fixing JS files"
    fix_ogvjs_dist $ASSETS_PATH "assets"
else
    echo "NOT fixing JS files (zimscraperlib not installed)"
fi