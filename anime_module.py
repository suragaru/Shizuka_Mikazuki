import aiohttp
import re

ANILIST_QUERY = """
query ($search: String) {
  Media(search: $search, type: ANIME) {
    id
    title {
      romaji
      english
      native
    }
    description
    genres
    format
    episodes
    status
    season
    startDate {
      year
      month
      day
    }
    endDate {
      year
      month
      day
    }
    averageScore
    popularity
    favourites
    studios {
      nodes {
        name
      }
    }
    coverImage {
      large
    }
    bannerImage
    siteUrl
  }
}
"""

def clean_html_tags(text):
    """Remove HTML tags from a given text."""
    clean = re.compile(r'<.*?>')
    return re.sub(clean, '', text)

async def fetch_anime_data(search_term):
    try:
        async with aiohttp.ClientSession() as session:
            url = 'https://graphql.anilist.co'
            payload = {
                'query': ANILIST_QUERY,
                'variables': {'search': search_term}
            }
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_message = await response.text()
                    print(f"Error: Received a {response.status} status code from AniList API. Response: {error_message}")
                    return None
    except aiohttp.ClientError as e:
        print(f"Client error occurred: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

