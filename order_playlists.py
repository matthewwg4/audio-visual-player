import os

def main(dir="."):

    for playlist in os.listdir(os.path.join(dir, "playlists")):
        filename = os.path.join(dir, "playlists", playlist)
        songs = []
        with open(filename, 'r') as file:
            next_line = file.readline()
            while next_line:
                songs.append(next_line.strip())
                next_line = file.readline()

        songs.sort(key=str.lower)
        write_str = '\n'.join(songs)
        with open(filename, 'w') as file:
            file.write(write_str)

if __name__ == '__main__':
    main()
