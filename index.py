from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
import httpx
from duckduckgo_search import DDGS
from tmdbv3api import TMDb, Movie

app = FastAPI()

# Allow all origins (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# TMDb API Setup
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
    sflix_results = []
    flimxy_results = []
    hdhub4u_results = []
    kuttymovies_results = []
    ddg_links = []

    # 1. IMDB info from TMDB
    try:
        results = movie_api.search(query)
        if results:
            first = results[0]
            imdb_data = {
                "title": first.title,
                "poster": f"https://image.tmdb.org/t/p/w500{first.poster_path}" if first.poster_path else None,
                "rating": first.vote_average,
                "release_year": str(first.release_date).split("-")[0],
                "overview": first.overview,
            }
    except:
        pass

    # 2. Scrape Flimxy
    try:
        url = f"https://flimxy.vip/?s={query.replace(' ', '+')}"
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
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

    # 3. Scrape HDHub4u
    try:
        url = f"https://hdhub4u.cricket/?s={query.replace(' ', '+')}"
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
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

    # 4. Scrape KuttyMovies
    try:
        url = f"https://kuttymovies.cc/?s={query.replace(' ', '+')}"
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
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

    # 5. Sflix fallback
    if not flimxy_results and not hdhub4u_results and not kuttymovies_results:
        try:
            url = f"https://sflix.to/search/{query.replace(' ', '%20')}"
            async with httpx.AsyncClient() as client:
                r = await client.get(url)
            soup = BeautifulSoup(r.text, "html.parser")
            items = soup.select("div.flw-item")
            for item in items:
                link = "https://sflix.to" + item.a["href"]
                title = item.select_one(".film-name").text.strip()
                img = item.img["data-src"]
                sflix_results.append({
                    "title": title,
                    "link": link,
                    "poster": img
                })
        except Exception as e:
            print("Sflix error:", e)

    # 6. DuckDuckGo links
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
        "sflix": sflix_results,
        "duckduckgo": ddg_links
    }
