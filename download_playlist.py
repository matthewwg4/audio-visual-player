import sys
import os
import signal
import subprocess
from multiprocessing import Process
import time

import convert
import order_playlists

from ytmusicapi.ytmusic import YTMusic

def download_playlist(dir, link, list_name):
    
    if list_name is None:
        list_name = "playlist"
    if list_name == "":
        list_name = "playlist"

    dir_base = dir
    folder = 'mp3-songs'
    directory = '{}/{}'.format(dir_base, folder)
    exists = os.path.exists(directory)
    i = -1
    while exists:
        i += 1
        exists = os.path.exists(directory + str(i))
    if i >= 0:
        folder += str(i)
        directory += str(i)

    os.mkdir(directory)

    print("Beginning download for playlist: {}\nDownloading from link: {}".format(list_name, link))

    playlistId = link[link.find("list=")+5:]
    playlistId_find = playlistId.find("&")
    if playlistId_find > 0:
        playlistId = playlistId[:playlistId_find]
    
    youtube = YTMusic()
    playlist_for_count = youtube.get_playlist(playlistId=playlistId, limit=1)
    playlist = youtube.get_playlist(playlistId=playlistId, limit=playlist_for_count['trackCount'])

    log_str = "--- WHILE OBTAINING PLAYLIST ---\n"
    log_str_orig_len = len(log_str)
    for track in playlist['tracks']:
        videoId = track['videoId']
        if videoId is None:
            log_str += "NOT FOUND: {}.\n".format(track['artists'][0]['name'] + " - " + track['title'])
            query = ""
            for artist in track['artists']:
                query += artist['name'] + " "
            query += track['title']
            search_list = youtube.search(query=query, filter='songs', limit=1, ignore_spelling=True)
            if len(search_list) == 0 or search_list[0]['videoId'] is None:
                query = track['artists'][0]['name'] + " " + track['title']
                search_list = youtube.search(query=query, filter='songs', limit=1, ignore_spelling=True)
                if len(search_list) == 0 or search_list[0]['videoId'] is None:
                    query = track['title']
                    search_list = youtube.search(query=query, filter='songs', limit=1, ignore_spelling=True)
                    if len(search_list) == 0 or search_list[0]['videoId'] is None:
                        search_list = youtube.search(query=query, filter='songs', limit=1, ignore_spelling=False)
            if len(search_list) > 0 and search_list[0]['videoId'] is not None:
                track['videoId'] = search_list[0]['videoId']
                track['artists'] = search_list[0]['artists']
                track['title'] = search_list[0]['title']
                videoId = track['videoId']
                log_str += "REPLACEMENT FOUND: {}.\n".format(track['artists'][0]['name'] + " - " + track['title'])
            else:
                log_str += "NO REPLACEMENT FOUND.\n"

    if len(log_str) == log_str_orig_len:
        log_str = ""
    
    proc = Process(target=download_tracks, args=(playlist, directory, dir_base, folder, list_name, log_str))
    proc.start()
    return proc

def download_tracks(playlist, directory, dir_base, folder, list_name, log_str="", kill_proc=True):

    track_count = len(playlist['tracks'])
    track_count_on = 1 # sys.stdout.write('\r%d%%' % x) sys.stdout.flush() prints x%

    log_str_pre_len = len(log_str)
    log_str += "--- WHILE DOWNLOADING PLAYLIST ---\n"
    log_str_orig_len = len(log_str)
    
    for track in playlist['tracks']:
        videoId = track['videoId']
        trackName = track['artists'][0]['name'] + " - " + track['title'] + ".mp3"
        slash_point = trackName.find("/")
        while slash_point >= 0:
            if slash_point == 0:
                trackName = "-" + trackName[1:]
            elif slash_point == len(trackName) - 1:
                trackName = trackName[:-1] + "-"
            else:
                trackName = trackName[:slash_point] + "-" + trackName[slash_point+1:]
            slash_point = trackName.find("/")
        slash_point = trackName.find("\\")
        while slash_point >= 0:
            if slash_point == 0:
                trackName = "-" + trackName[1:]
            elif slash_point == len(trackName) - 1:
                trackName = trackName[:-1] + "-"
            else:
                trackName = trackName[:slash_point] + "-" + trackName[slash_point+1:]
            slash_point = trackName.find("\\")
        print("({}/{}) Downloading: {}".format(track_count_on, track_count, trackName))
        if videoId is not None:
            music_url = 'https://music.youtube.com/watch?v=' + videoId
            results = subprocess.run(['youtube-dl', '-x', '-q', '--audio-format', 'mp3', '--output', trackName, music_url], cwd=directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output_log = results.stdout.decode('utf-8') + results.stderr.decode('utf-8')
            if (len(output_log) > 0):
                error_msg = "ERROR while downloading {}".format(trackName)
                print(error_msg)
                log_str += error_msg + ".\n"
        else:
            error_msg = "ERROR: Could not download {}".format(trackName)
            print(error_msg)
            log_str += error_msg + ".\n"

        track_count_on += 1

    convert.convert_songs_to_data(directory_base=dir_base, mp3_folder=folder, playlist_name=list_name)

    os.rmdir(directory)

    order_playlists.main(dir_base)
    print("Playlist download complete")
    if len(log_str) == log_str_orig_len:
        if log_str_pre_len == 0:
            print("No errors while downloading")
        else:
            print(log_str[:log_str_pre_len-1])
    else:
        print(log_str[:-1])

    pid = os.getpid()
    if kill_proc:
        os.setpgid(pid, pid)
        os.killpg(pid, signal.SIGKILL)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Missing directory or link to playlist")
        exit(-1)
    list_name = "playlist"
    if len(sys.argv) > 3:
        list_name = sys.argv[3]

    download_playlist(sys.argv[1], sys.argv[2], list_name)
