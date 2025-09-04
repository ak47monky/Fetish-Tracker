import requests
import json

# Define the AniList API endpoint
url = 'https://graphql.anilist.co'

# The GraphQL query to search for anime titles
query = '''
query ($search: String, $page: Int, $perPage: Int) {
  Page (page: $page, perPage: $perPage) {
    media (search: $search, type: ANIME) {
      id
      title {
        romaji
        english
      }
      episodes
    }
  }
}
'''

# The variables to pass to the query (your search term)
variables = {
    'search': 'One Piece', # Replace with the anime you want to search for
    'page': 1,
    'perPage': 5
}

# Make the request to the API
response = requests.post(url, json={'query': query, 'variables': variables})

# Check if the request was successful
if response.status_code == 200:
    data = response.json()
    # Print the fetched titles
    print("Found these titles:")
    for anime in data['data']['Page']['media']:
        romaji_title = anime['title']['romaji']
        english_title = anime['title']['english']
        episodes = anime['episodes']
        
        print(f"  - {romaji_title} ({english_title}) | Episodes: {episodes}")
else:
    print(f"Error fetching data. Status code: {response.status_code}")
    print(response.text)