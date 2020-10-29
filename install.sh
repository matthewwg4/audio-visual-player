# install homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"

# install python 3
brew install python3

# install ffmpeg (dependency of python library pydub)
brew install ffmpeg --with-libvorbis --with-sdl2 --with-theora

# install python libraries
pip3 install numpy
pip3 install librosa
pip3 install vlc
pip3 install pydub
pip3 install serial
pip3 install spotdl

# rewrite player.c with appropriate path
python3 player_writer.py

# create executable and place on desktop
clang player.c -o ~/Desktop/"Audio-Visual Player"