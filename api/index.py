from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
import httpx
from duckduckgo_search import DDGS
from tmdbv3api import TMDb, Movie
import os
import asyncio

app = FastAPI()
# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# TMDB setup - Use environment variable if available
tmdb = TMDb()
tmdb.api_key = os.environ.get("TMDB_API_KEY", "3a08a646f83edac9a48438ac670a78b2")
tmdb.language = "en"
movie_api = Movie()

# Configure httpx client with shorter timeouts
client = httpx.AsyncClient(timeout=10.0)

@app.get("/")
def root():
    return {"status": "Universal Movie & TV Series Scraper API is running!"}

async def get_flimxy_download_links(url):
    """Extract download links from a Flimxy movie page"""
    try:
        r = await client.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        download_links = []
        
        # Look for download buttons and links
        download_elements = soup.select("div.dlinks a") or soup.select("div.download a") or soup.select("a.download")
        
        for element in download_elements:
            if element.get('href') and not element['href'].startswith('#'):
                download_links.append({
                    "quality": element.text.strip() or "Unknown Quality",
                    "link": element['href']
                })
        
        return download_links
    except Exception as e:
        print(f"Error getting Flimxy download links: {e}")
        return []

async def get_hdhub4u_download_links(url):
    """Extract download links from a HDHub4u movie page"""
    try:
        r = await client.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        download_links = []
        
        # Look for download buttons and links
        download_elements = soup.select("div.dwnlds a") or soup.select("div.download-links a")
        
        for element in download_elements:
            if element.get('href') and not element['href'].startswith('#'):
                quality = element.text.strip()
                if not quality:
                    quality_span = element.select_one("span")
                    if quality_span:
                        quality = quality_span.text.strip()
                
                download_links.append({
                    "quality": quality or "Unknown Quality",
                    "link": element['href']
                })
        
        return download_links
    except Exception as e:
        print(f"Error getting HDHub4u download links: {e}")
        return []

async def get_kuttymovies_download_links(url):
    """Extract download links from a KuttyMovies movie page"""
    try:
        r = await client.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        download_links = []
        
        # Look for download buttons and links
        download_elements = soup.select("div.dlink a") or soup.select("div.download a") or soup.select("a.download")
        
        for element in download_elements:
            if element.get('href') and not element['href'].startswith('#'):
                download_links.append({
                    "quality": element.text.strip() or "Unknown Quality",
                    "link": element['href']
                })
        
        return download_links
    except Exception as e:
        print(f"Error getting KuttyMovies download links: {e}")
        return []

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
    except Exception as e:
        print(f"TMDB error: {e}")
    
    # 2. Flimxy scraper
    try:
        url = f"https://flimxy.vip/?s={query.replace(' ', '+')}"
        r = await client.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        posts = soup.select("div.result-item")
        
        for index, post in enumerate(posts[:3]):  # Limit to first 3 results to avoid timeouts
            title = post.select_one("h3").text.strip()
            link = post.a["href"]
            img = post.img["src"] if post.img else ""
            
            flimxy_results.append({
                "title": title,
                "link": link,
                "poster": img,
                "download_links": []  # Initialize empty, will be filled later
            })
    except Exception as e:
        print(f"Flimxy error: {e}")
    
    # 3. HDHub4u scraper
    try:
        url = f"https://hdhub4u.cricket/?s={query.replace(' ', '+')}"
        r = await client.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        posts = soup.select("div.result-item")
        
        for index, post in enumerate(posts[:3]):  # Limit to first 3 results
            title = post.select_one("h3").text.strip()
            link = post.a["href"]
            img = post.img["src"] if post.img else ""
            
            hdhub4u_results.append({
                "title": title,
                "link": link,
                "poster": img,
                "download_links": []  # Initialize empty, will be filled later
            })
    except Exception as e:
        print(f"HDHub4u error: {e}")
    
    # 4. KuttyMovies scraper
    try:
        url = f"https://kuttymovies.cc/?s={query.replace(' ', '+')}"
        r = await client.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        posts = soup.select("div.result-item")
        
        for index, post in enumerate(posts[:3]):  # Limit to first 3 results
            title = post.select_one("h3").text.strip()
            link = post.a["href"]
            img = post.img["src"] if post.img else ""
            
            kuttymovies_results.append({
                "title": title,
                "link": link,
                "poster": img,
                "download_links": []  # Initialize empty, will be filled later
            })
    except Exception as e:
        print(f"KuttyMovies error: {e}")
    
    # 5. DuckDuckGo fallback links
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query + " movie download", max_results=5)  # Limit to 5 results
            for r in results:
                ddg_links.append({"link": r.get("href")})
    except Exception as e:
        print(f"DuckDuckGo error: {e}")
    
    # Fetch download links for the first result of each site (to avoid timeouts)
    download_tasks = []
    
    if flimxy_results:
        download_tasks.append(get_flimxy_download_links(flimxy_results[0]["link"]))
    if hdhub4u_results:
        download_tasks.append(get_hdhub4u_download_links(hdhub4u_results[0]["link"]))
    if kuttymovies_results:
        download_tasks.append(get_kuttymovies_download_links(kuttymovies_results[0]["link"]))
    
    if download_tasks:
        download_results = await asyncio.gather(*download_tasks, return_exceptions=True)
        
        # Update results with download links
        result_index = 0
        if flimxy_results:
            if isinstance(download_results[result_index], list):
                flimxy_results[0]["download_links"] = download_results[result_index]
            result_index += 1
            
        if hdhub4u_results:
            if isinstance(download_results[result_index], list):
                hdhub4u_results[0]["download_links"] = download_results[result_index]
            result_index += 1
            
        if kuttymovies_results:
            if isinstance(download_results[result_index], list):
                kuttymovies_results[0]["download_links"] = download_results[result_index]
    
    await client.aclose()  # Close the httpx client
    
    return {
        "imdb": imdb_data,
        "flimxy": flimxy_results,
        "hdhub4u": hdhub4u_results,
        "kuttymovies": kuttymovies_results,
        "duckduckgo": ddg_links
    }
