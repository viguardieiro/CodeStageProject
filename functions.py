# Import the libraries
import os
import pandas as pd
import json
import spotipy
import spotipy.util as util

def GetUserTopSongs(username, CLIENT_ID, CLIENT_SECRET, redirect_uri)
    # Authorization flow
    scope = 'user-top-read'
    token = util.prompt_for_user_token(username, scope, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=redirect_uri)

    if token:
        sp = spotipy.Spotify(auth=token)
        results = sp.current_user_top_tracks(limit=50,offset=0,time_range='medium_term')
        for song in range(50):
            list1 = []
            list1.append(results)
            with open('top50_data.json', 'w', encoding='utf-8') as f:
                json.dump(list1, f, ensure_ascii=False, indent=4)

        # Open the JSON file to Python objects
        with open('top50_data.json') as f:
            data = json.load(f)

        list_of_results = data[0]["items"]
        list_of_artist_names = []
        list_of_artist_uri = []
        list_of_song_names = []
        list_of_song_uri = []
        list_of_durations_ms = []
        list_of_explicit = []
        list_of_albums = []
        list_of_popularity = []

        for result in list_of_results:
            result["album"]
            this_artists_name = result["artists"][0]["name"]
            list_of_artist_names.append(this_artists_name)
            this_artists_uri = result["artists"][0]["uri"]
            list_of_artist_uri.append(this_artists_uri)
            list_of_songs = result["name"]
            list_of_song_names.append(list_of_songs)
            song_uri = result["uri"]
            list_of_song_uri.append(song_uri)
            list_of_duration = result["duration_ms"]
            list_of_durations_ms.append(list_of_duration)
            song_explicit = result["explicit"]
            list_of_explicit.append(song_explicit)
            this_album = result["album"]["name"]
            list_of_albums.append(this_album)
            song_popularity = result["popularity"]
            list_of_popularity.append(song_popularity)

        # Convert the pulled content to a pandas df
        all_songs = pd.DataFrame(
            {'artist': list_of_artist_names,
             'artist_uri': list_of_artist_uri,
             'song': list_of_song_names,
             'song_uri': list_of_song_uri,
             'duration_ms': list_of_durations_ms,
             'explicit': list_of_explicit,
             'album': list_of_albums,
             'popularity': list_of_popularity

            })

        #Making into A CSV
        all_songs.to_csv('UserSongs/'+username+'.csv')
        return all_songs
    else:
        print("Can't get token for", username)
        return
        
