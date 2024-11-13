import os
import requests
from dotenv import load_dotenv 
from pymongo import MongoClient
from datetime import datetime

# Charger les variables d'environnement pour protéger les informations sensibles
load_dotenv()

# Configurations de MongoDB
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "social_media"
COLLECTION_NAME = "posts"

# Connexion à MongoDB via pymongo
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Configurations d'API Facebook
ACCESS_TOKEN = os.getenv("myaccesstoken")
FB_GRAPH_API_URL = "https://graph.facebook.com/v14.0"

def fetch_facebook_posts(query, limit=10):
    """
    Cette fonction récupère les publications Facebook contenant le mot-clé défini.
    """
    url = f"{FB_GRAPH_API_URL}/search"
    params = {
        'access_token': ACCESS_TOKEN,
        'q': query,
        'type': 'page',  # Pour chercher parmi les pages, ou utilisez 'post' pour les publications
        'fields': f'id,name,posts.limit({limit}){{message,full_picture,comments{{message}}}}'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('data', [])
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la requête vers l'API Facebook : {e}")
        return []

def save_post_to_mongodb(post_data):
    """
    Sauvegarde une publication dans MongoDB via pymongo.
    """
    post = {
        'page_id': post_data['page_id'],
        'page_name': post_data['page_name'],
        'text': post_data.get('text'),
        'image_url': post_data.get('image_url'),
        'comments': post_data.get('comments', []),
        'created_at': datetime.utcnow()  # Store the creation time of the document
    }
    try:
        collection.insert_one(post)  # Insert the post as a document in the collection
        print(f"Publication sauvegardée dans MongoDB : {post_data['page_name']}")
    except Exception as e:
        print(f"Erreur lors de l'insertion dans MongoDB: {e}")

def process_and_store_posts(posts):
    """
    Transforme et stocke chaque publication de la liste dans MongoDB.
    """
    for post in posts:
        for post_detail in post.get('posts', {}).get('data', []):
            post_data = {
                'page_id': post.get('id'),
                'page_name': post.get('name'),
                'text': post_detail.get('message'),
                'image_url': post_detail.get('full_picture'),
                'comments': [comment['message'] for comment in post_detail.get('comments', {}).get('data', [])]
            }
            save_post_to_mongodb(post_data)

def main():
    query = "World Cup 2024" 
    print(f"Recherche des publications concernant : {query}")
    posts = fetch_facebook_posts(query)
    process_and_store_posts(posts)

if __name__ == "__main__":
    main()
