'''
Youtube --> Spotify Playlist Converter
By: Franco Bonilla
Use: Transfers Youtube & Youtube Music playlists to spotify
'''


'''
"Human" Steps for 1 playlist:
1. Open Youtube
    - Check if logged in
    - Go to playlist, get song
2. Open Spotify
    - Check if logged in
    - Create new playlist
    - Search for song from Youtube playlist
    - Add song to Spotify playlist 
'''



from distutils.log import error
import json
from logging import exception
import requests
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import youtube_dl
from exceptions import ResponseException
from secrets import spotify_user, spotify_token



# gives youtube client
def into_youtube():
    '''
    ALL FROM YOUTUBE DATA API
    '''


    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "client_secret.json"

    scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
    credentials = flow.run_console()

    youtube_client = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)

    return youtube_client



# gives a song uri
def search_spotify_song(song_name, my_spot_token):
    '''
    get_youtube_song --> song_name, singer
    main --> my_spot_token
    '''

    # search info for song
    song_search_address = "https://api.spotify.com/v1/search?q={}&type=track&include_external=false".format(song_name)

    # search for song
    song_result = requests.get(song_search_address, 
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(my_spot_token)
        }
    )
    # make result useful
    song_result_useful = song_result.json()

    # get song uris
    song_uri = song_result_useful["tracks"]["items"][0]["uri"]
    
    # give song uri
    return song_uri



# gives dict of all playlists from a youtube account
def get_youtube_songs(youtube_client, my_spot_token):

    # make a dict and list to hold playlist_id(key): [playlist_name, song_id]
    playlists_dict = {}

    # get playlist name + id
    # Ex: {"Hot Girl Summer": [["Potato Body","23nko42ml4m"], ["Tater tot Dog", "132344444njm54jn"], ["Sausage Energy", "53krm4r3k3"]]}
    playlists_request = youtube_client.playlists().list(part="snippet", maxResults=100, mine=True)
    playlists_info = playlists_request.execute()
    for item in playlists_info["items"]:
        print(item["snippet"]["title"])
        playlist_id = item["id"]
        playlist_clean_song_list = []
        # for each playlist, get the songs
        songs_request = youtube_client.playlistItems().list(part="id,snippet", playlistId=playlist_id)
        songs_info = songs_request.execute()
        for itemA in songs_info["items"]:
            print(itemA["snippet"]["title"])
            clean_song_info = []
            # go to video
            yt_url = "https://www.youtube.com/watch?v={}".format(itemA["id"])
            # get song title + artist from video
            try:
                spotify_uri = search_spotify_song(itemA["snippet"]["title"], my_spot_token)
                clean_song_info.append(itemA["snippet"]["title"])
                clean_song_info.append(spotify_uri)
                playlist_clean_song_list.append(clean_song_info)
            except Exception as e:
                print(e)
                print("Not an available song.")

        # create dict w/ playlist id as key, and title and artists as value
        playlists_dict[item["snippet"]["title"]] = playlist_clean_song_list

    print(playlists_dict)
    return playlists_dict


# gives playlist id of new playlist in Spotify
def make_spotify_playlist(playlist_name, the_user, my_spot_token):
    '''
    into_youtube_playlist --> playlist_name
    into_spotify --> the_user
    main --> my_spot_token
    '''
    
    # set details of new playlist
    new_playlist_info = json.dumps({
        "name": playlist_name,
        "description": playlist_name,
        "public": True
    })
  
    # create new playlist
    playlist_maker_address = "https://api.spotify.com/v1/users/{user_id}/playlists".format(user_id = the_user)
    playlist_info = requests.post(playlist_maker_address, data=new_playlist_info, 
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(my_spot_token)
        }
    )
    # make playlist info useful
    playlist_info_useful = playlist_info.json()
    print(playlist_info_useful)
    # give playlist id
    return playlist_info_useful["id"]


# adds a song to a playlist
def add_spotify_song(song_uri, playlist_id):


    # add all songs into new playlist
    song_uri_list = []
    song_uri_list.append(song_uri)
    try:
        request_data = json.dumps(song_uri_list)

        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(
            playlist_id)

        response = requests.post(
            query,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )
    except:
        print("Not a valid track.")


    response_json = response.json()
    return response_json



def main():

     youtube_client = into_youtube()
     my_spot_id = spotify_user
     my_spot_token = spotify_token

     # make dictionary with all playlists and songs in playlist
     songs_info = get_youtube_songs(youtube_client, my_spot_token)

     # make playlists in Spotify
     # put playlist ids in list
     for playlist_title,songs in songs_info.items():
        spot_playlist_id = make_spotify_playlist(playlist_title, my_spot_id, my_spot_token)
        for i in range(len(songs)):
            answer = add_spotify_song(songs[i][1], spot_playlist_id)
    

if __name__ == "__main__":
     main()
     print("Complete! You are the most welcome.")