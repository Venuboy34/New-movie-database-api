from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
import httpx
from duckduckgo_search import DDGS
from tmdbv3api import TMDb, Movie

app = FastAPI()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# TMDB setup
tmdb = TMDb()
tmdb.api_key = "3a08a646f83edac9a48438ac670a78b2"
tmdb.language = "en"
movie_api = Movie()

@app.get("/")
def root():
    return {"status": "Universal Movie & TV Series Scraper API is running!"}

@app.get("/search")
async def search_movies(query: str = Query(...)):
    imdb_data = {}
    flimxy_results = []
    hdhub4u_results = []
    kuttymovies_results = []
    ddg_links = []

    # 1. IMDB/TMDB Data
    try:
        results = movie_api.search(query)
        if results:
            first = results[0]
            imdb_data = {
                "title": first.title,
                "poster": f"https://image.tmdb.org/t/p/w500{first.poster_path}" if first.poster_path else None,
                "rating": first.vote_average,
                "release_year": str(first.release_date).split("-")[0] if first.release_date else "",
                "overview": first.overview,
            }
    except:
        pass

    # 2. Flimxy scraper
    try:
        url = f"https://flimxy.lat/?s={query.replace(' ', '+')}"
        async with httpx.AsyncClient() as client:
            r = await client.get(url, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        posts = soup.select("div.result-item")
        for post in posts:
            title = post.select_one("h3").text.strip()
            link = post.a["href"]
            img = post.img["src"]
            flimxy_results.append({
                "title": title,
                "link": link,
                "poster": img
            })
    except Exception as e:
        print("Flimxy error:", e)

    # 3. HDHub4u scraper
    try:
        url = f"https://hdhub4u.lat/?s={query.replace(' ', '+')}"
        async with httpx.AsyncClient() as client:
            r = await client.get(url, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        posts = soup.select("div.result-item")
        for post in posts:
            title = post.select_one("h3").text.strip()
            link = post.a["href"]
            img = post.img["src"]
            hdhub4u_results.append({
                "title": title,
                "link": link,
                "poster": img
            })
    except Exception as e:
        print("HDHub4u error:", e)

    # 4. KuttyMovies scraper
    try:
        url = f"https://kuttymovies.day/?s={query.replace(' ', '+')}"
        async with httpx.AsyncClient() as client:
            r = await client.get(url, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        posts = soup.select("div.result-item")
        for post in posts:
            title = post.select_one("h3").text.strip()
            link = post.a["href"]
            img = post.img["src"]
            kuttymovies_results.append({
                "title": title,
                "link": link,
                "poster": img
            })
    except Exception as e:
        print("KuttyMovies error:", e)

    # 5. DuckDuckGo fallback links
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query + " movie download", max_results=10)
            for r in results:
                ddg_links.append({"link": r.get("href")})
    except:
        pass

    return {
        "imdb": imdb_data,
        "flimxy": flimxy_results,
        "hdhub4u": hdhub4u_results,
        "kuttymovies": kuttymovies_results,
        "duckduckgo": ddg_links
    }
