import requests
import json

# Define the AniList API endpoint
url = 'https://graphql.anilist.co'

# The GraphQL query to get all the details for a specific anime
query = '''
query ($id: Int) {
  Media(id: $id, type: ANIME) {
    title {
      romaji
      english
    }
    format
    status
    description(asHtml: false)
    startDate {
      year
      month
      day
    }
    episodes
    duration
    genres
    coverImage {
      large
    }
    trailer {
      id
      site
    }
    relations {
      edges {
        relationType
        node {
          id
          title {
            romaji
            english
          }
          format
          episodes
          coverImage {
            large
          }
        }
      }
    }
  }
}
'''

# The variable to pass to the query (we use the ID instead of a search)
# This ID is for Grand Blue, which you just added!
variables = {
    'id': 21
}

# Make the request to the API
response = requests.post(url, json={'query': query, 'variables': variables})

# Check if the request was successful
if response.status_code == 200:
    data = response.json()
    anime_data = data['data']['Media']
    
    # Print the fetched details
    print("--- Anime Details ---")
    print(f"Title: {anime_data['title']['english']} ({anime_data['title']['romaji']})")
    print(f"Status: {anime_data['status']}")
    print(f"Format: {anime_data['format']}")
    print(f"Episodes: {anime_data['episodes']}")
    print(f"Genres: {', '.join(anime_data['genres'])}")
    print(f"Description: {anime_data['description'][:200]}...") # Print first 200 chars
    
    # Print related anime
    print("\n--- Related Anime ---")
    for edge in anime_data['relations']['edges']:
        relation_type = edge['relationType'].replace("_", " ")
        related_anime = edge['node']
        print(f"  - {relation_type}: {related_anime['title']['romaji']}")
else:
    print(f"Error fetching data. Status code: {response.status_code}")
    print(response.text)