# Import the libraries
import os
import pandas as pd
import json
import spotipy
import spotipy.util as util
from sklearn.decomposition import PCA 
from spotipy.oauth2 import SpotifyClientCredentials
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
import random
from pandas.io.json import json_normalize
import os

class RecommendSongs():
    def __init__(self, username, CLIENT_ID, CLIENT_SECRET, redirect_uri, playlist_name, playlist_description, users_directory = 'UserSongs'):
        self.username = username
        self.CLIENT_ID = CLIENT_ID
        self.CLIENT_SECRET = CLIENT_SECRET
        self.redirect_uri = redirect_uri
        self.users = 0
        self.all_songs = []
        self.audio_feat = []
        self.users_directory = 'UserSongs'
        self.recommended_songs = []
        self.playlist_name = playlist_name
        self.playlist_description = playlist_description
        self.sp = []

    def GetUserTopSongs(self, new_username):
        # Authorization flow
        scope = 'user-top-read'
        token = util.prompt_for_user_token(new_username, scope, client_id=self.CLIENT_ID, client_secret=self.CLIENT_SECRET, redirect_uri=self.redirect_uri)

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
            all_songs.to_csv(self.users_directory+new_username+'.csv')
            return all_songs
        else:
            print("Can't get token for", new_username)
            return

    def JoinUsersFavSongs(self):
        all_songs = []

        user_id = 0
        for filename in os.listdir(self.users_directory):
            if filename.endswith(".csv"):
                user_songs = pd.read_csv(os.path.join(self.users_directory, filename))
                user_songs['user'] = user_id
                user_id += 1
                all_songs.append(user_songs)

        self.users = user_id
                
        all_songs = pd.concat(all_songs)
        all_songs.reset_index(drop=True,inplace=True)

        return all_songs

    def ExtractAudioFeatures(self):
        # Authorization flow
        scope = 'user-top-read'
        token = util.prompt_for_user_token(self.username, scope, client_id=self.CLIENT_ID, client_secret=self.CLIENT_SECRET, redirect_uri=self.redirect_uri)

        if token:
            sp = spotipy.Spotify(auth=token)
        else:
            print("Can't get token for", self.username)

        audio_feat = []
        for song in self.all_songs['song_uri']:
            row = pd.DataFrame(sp.audio_features(tracks=[song]))
            audio_feat.append(row)
        audio_feat = pd.concat(audio_feat)
        return audio_feat

    def CleanData(self):
        self.audio_feat.drop(['type','track_href','analysis_url','time_signature','duration_ms','uri','key','mode'],1,inplace=True)
        self.audio_feat.set_index('id',inplace=True)

    def NormalizeFeatures(self):
        columns = ['danceability','energy','speechiness','acousticness','valence','tempo','instrumentalness','liveness','loudness']
        scaler = MinMaxScaler()
        scaler.fit(self.audio_feat[columns])
        self.audio_feat[columns] = scaler.transform(self.audio_feat[columns])

    def GenRecomendations(self, sp):
        clusters = self.users*10
        kmeans = KMeans(n_clusters=clusters)
        kmeans.fit(self.audio_feat)

        pca = PCA(3) 
        pca.fit(self.audio_feat) 

        pca_data = pd.DataFrame(pca.transform(self.audio_feat)) 

        scaler = MinMaxScaler()
        scaled = scaler.fit_transform(self.audio_feat)
        y_kmeans = kmeans.fit_predict(scaled)

        # Updating dataframe with assigned clusters 
        self.audio_feat['cluster'] = y_kmeans
        self.audio_feat['artist'] = self.all_songs.artist.tolist()
        self.audio_feat['title'] = self.all_songs.song.tolist()
        self.audio_feat['user'] = self.all_songs.user.tolist()

        # Removing clusters that only have one song in them
        delete_clusters = []
        cluster = 0
        while cluster < (len(self.audio_feat.cluster.unique())-1):
            if self.audio_feat.groupby('cluster').count().loc[cluster].danceability == 1:
                delete_clusters.append(cluster)

            cluster+=1

        self.audio_feat.reset_index(inplace=True)

        i = 0
        while i < (len(self.audio_feat.cluster.unique())-1):
            if self.audio_feat.loc[[i]].cluster.tolist()[0] in delete_clusters:
                self.audio_feat.drop(i,0,inplace=True)
            i+=1

        self.audio_feat.set_index('id',inplace=True)

        # Create list of lists of song ids to put into recommendation function
        i=0
        list_of_recs = [0]*len(self.audio_feat.groupby('cluster').count())
        while i<len(self.audio_feat.groupby('cluster').count()):
            list_of_recs[i] = self.audio_feat.loc[self.audio_feat['cluster'] == i].index.tolist()
            i+=1

        list_of_recs = [ele for ele in list_of_recs if ele != []] 

        # Adjust list for clusters so that each cluster has a maximum of 5 seed songs
        j = 0
        adj_list_of_recs = [0]*len(list_of_recs)
        while j<len(list_of_recs):
            if 0 < len(list_of_recs[j]) < 6:
                adj_list_of_recs[j] = list_of_recs[j]
            elif len(list_of_recs[j]) > 5:
                adj_list_of_recs[j] = random.sample(list_of_recs[j], 5)
            j += 1

       #Getting 1 recommended song from each cluster with less than 4 songs, 2 recommended songs from each cluster with 4-5 songs
        k = 0
        list_of_recommendations = [0]*len(list_of_recs)
        while k < len(list_of_recs):
            if len(adj_list_of_recs[k]) < 4:
                list_of_recommendations[k] = sp.recommendations(seed_tracks=adj_list_of_recs[k],limit=1)
            else:
                list_of_recommendations[k] = sp.recommendations(seed_tracks=adj_list_of_recs[k],limit=2)
            k += 1

        pd.json_normalize(list_of_recommendations[15], record_path='tracks').id

        list_of_recommendations_converted = [0]*len(list_of_recs)

        l = 0
        while l < len(list_of_recs):
            list_of_recommendations_converted.append(pd.json_normalize(list_of_recommendations[l], record_path='tracks').id.tolist())
            l += 1

        no_integers = [x for x in list_of_recommendations_converted if not isinstance(x, int)]
        recommended_songs = [item for elem in no_integers for item in elem]
        
        return recommended_songs

    def CreateNewPlaylist(self, sp):
        playlists = sp.user_playlist_create(self.username, self.playlist_name, description = self.playlist_description)

    def FetchPlaylists(self, sp):        
        id = []
        name = []
        num_tracks = []

        # Make the API request
        playlists = sp.user_playlists(self.username)
        for playlist in playlists['items']:
            id.append(playlist['id'])
            name.append(playlist['name'])
            num_tracks.append(playlist['tracks']['total'])

        # Create the final df   
        df_playlists = pd.DataFrame({"id":id, "name": name, "#tracks": num_tracks})
        return df_playlists

    def PopulatePlaylist(self, sp, extracted_id, list_of_songs):
        sp.user_playlist_add_tracks(self.username, extracted_id, list_of_songs, position=None)

    def CreatePlaylist(self, sp):
        self.CreateNewPlaylist(sp)

        extracted_id = self.FetchPlaylists(sp).id[0]

        self.PopulatePlaylist(sp, extracted_id, self.recommended_songs)
        
    def Recommend(self):
        # Authorization flow
        scope = 'user-top-read'
        token = util.prompt_for_user_token(self.username, scope, client_id=self.CLIENT_ID, client_secret=self.CLIENT_SECRET, redirect_uri=self.redirect_uri)

        if token:
            sp = spotipy.Spotify(auth=token)
        else:
            print("Can't get token for", username)
    
        self.all_songs = self.JoinUsersFavSongs()
        self.audio_feat = self.ExtractAudioFeatures()
        self.CleanData()
        self.NormalizeFeatures()
        self.recommended_songs = self.GenRecomendations(sp)
        
        # Authorization flow
        scope = "playlist-modify-public"
        token = util.prompt_for_user_token(self.username, scope, client_id=self.CLIENT_ID, client_secret=self.CLIENT_SECRET, redirect_uri=self.redirect_uri)
        
        if token:
            sp = spotipy.Spotify(auth=token)
        else:
            print("Can't get token for", self.username)
        
        self.CreatePlaylist(sp)