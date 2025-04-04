from flask import Flask, request, Response
import requests
from bs4 import BeautifulSoup
import json

app = Flask(__name__)
TMDB_API_KEY = "3a08a646f83edac9a48438ac670a78b2"

def pretty_json(data):
    return Response(json.dumps(data, indent=2), mimetype="application/json")

@app.route("/")
def home():
    return pretty_json({"status": "Universal Movie & TV Series Scraper API is running!"})

@app.route("/search")
def search():
    query = request.args.get("q")
    if not query:
        return pretty_json({"error": "Missing search query"})

    return pretty_json({
        "imdb": fetch_tmdb(query),
        "sflix": search_sflix(query),
        "flimxy": search_duckduckgo(query + " site:flimxy.cc"),
        "hdhub4u": search_hdhub4u(query),
        "kuttymovies": search_kuttymovies(query),
        "duckduckgo": search_duckduckgo(query)
    })

def fetch_tmdb(query):
    try:
        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"
        res = requests.get(url, timeout=10).json()
        if not res["results"]:
            return {"error": "No TMDB data found"}
        movie = res["results"][0]
        return {
            "title": movie["title"],
            "poster": f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie["poster_path"] else None,
            "rating": movie["vote_average"],
            "release_year": movie["release_date"][:4] if movie.get("release_date") else "N/A",
            "overview": movie["overview"]
        }
    except Exception as e:
        return {"error": str(e)}

def search_sflix(query):
    try:
        url = f"https://sflix.to/search/{query.replace(' ', '%20')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        data = []
        for item in soup.select(".flw-item"):
            title_tag = item.select_one(".film-name a")
            img_tag = item.select_one("img")
            if not title_tag or not img_tag:
                continue
            data.append({
                "title": title_tag.text.strip(),
                "link": "https://sflix.to" + title_tag["href"],
                "poster": img_tag.get("data-src") or img_tag.get("src")
            })
        return data
    except Exception as e:
        return {"error": str(e)}

def search_hdhub4u(query):
    try:
        url = f"https://hdhub4u.cricket/?s={query.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        data = []
        for item in soup.select(".post"):
            title_tag = item.select_one("h3 a")
            img_tag = item.select_one("img")
            if not title_tag or not img_tag:
                continue
            data.append({
                "title": title_tag.text.strip(),
                "link": title_tag["href"],
                "poster": img_tag.get("data-src") or img_tag.get("src")
            })
        return data
    except Exception as e:
        return {"error": str(e)}

def search_kuttymovies(query):
    try:
        url = f"https://1kuttymovies.cc/search/{query.replace(' ', '%20')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        data = []
        for item in soup.select(".flw-item"):
            title_tag = item.select_one(".film-name a")
            img_tag = item.select_one("img")
            if not title_tag or not img_tag:
                continue
            data.append({
                "title": title_tag.text.strip(),
                "link": "https://1kuttymovies.cc" + title_tag["href"],
                "poster": img_tag.get("data-src") or img_tag.get("src")
            })
        return data
    except Exception as e:
        return {"error": str(e)}

def search_duckduckgo(query):
    try:
        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        data = []
        for result in soup.select(".result__url"):
            link = result.text.strip()
            if not link.startswith("http"):
                link = "https://" + link
            data.append({"link": link})
        return data
    except Exception as e:
        return {"error": str(e)}

# Required by Vercel
app = app
