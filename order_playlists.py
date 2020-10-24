import os

def main():

    for list in os.listdir("playlists"):
        filename = os.path.join("playlists", list)
        songs = []
        with open(filename, 'r') as file:
            next_line = file.readline()
            while next_line:
                songs.append(next_line.strip())
                next_line = file.readline()

        songs.sort()
        str = '\n'.join(songs)
        with open(filename, 'w') as file:
            file.write(str)

if __name__ == '__main__':
    main()
