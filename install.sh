# install homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"

# install python 3
brew install python@3.7

# install ffmpeg and youtube-dl
brew install ffmpeg 
brew install youtube-dl

# install python libraries
pip3 install numpy
pip3 install python-vlc
pip3 install librosa
pip3 install pyserial
pip3 install ytmusicapi

# rewrite player.c with appropriate path
python3 player_writer.py

# create executable and place on desktop
clang player.c -o ~/Desktop/"Audio-Visual Player"