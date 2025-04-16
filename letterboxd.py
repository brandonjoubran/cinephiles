from flask import Flask, render_template, redirect, url_for, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent.futures
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
import time

from config import load_config
from cache import is_cache_valid, load_cache, save_cache, CACHE_FILE
from scraper import get_all_user_logs
from utils import expand_short_url, build_stats, slugify
from db import get_watchlist_sheet, get_users_sheet, get_nominations_sheet, get_selected_sheet

app = Flask(__name__)

# -------------- Config ------------------
CONFIG = load_config()
USERNAMES = CONFIG['usernames']
MOVIES = CONFIG['movies']
load_dotenv()

def get_poster(movie_title, release_year):
    # Your TMDb API key
    #API_KEY = os.getenv('API_KEY')
    API_KEY = os.environ.get('API_KEY', os.getenv('API_KEY'))

    # Movie title and release year
    #movie_title = 'The Count of Monte Cristo'
    #release_year = 2024
    print(movie_title, release_year)
    # Search for the movie on TMDb
    search_url = f'https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={movie_title}&year={release_year}'
    search_response = requests.get(search_url).json()

    # Check if the movie was found
    if search_response['results']:
        # Assuming the first result is the correct one
        movie = search_response['results'][0]
        print(search_response)
        movie_id = movie['id']
        movie_title = movie['title']
        movie_release_date = movie['release_date']
        
        # Get movie details using the movie ID
        details_url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}'
        details_response = requests.get(details_url).json()
        
        # Construct the full poster URL
        poster_path = details_response['poster_path']
        poster_url = f'https://image.tmdb.org/t/p/w500{poster_path}'
        
        print(f"Movie: {movie_title} ({movie_release_date})")
        print(f"Poster URL: {poster_url}")
    else:
        print("Movie not found.")
    return poster_url

def get_poster(movie_id):
    # Your TMDb API key
    #API_KEY = os.getenv('API_KEY')
    API_KEY = os.environ.get('API_KEY', os.getenv('API_KEY'))
        
    # Get movie details using the movie ID
    details_url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}'
    details_response = requests.get(details_url).json()
    
    # Construct the full poster URL
    poster_path = details_response['poster_path']
    poster_url = f'https://image.tmdb.org/t/p/w500{poster_path}'
    
    if poster_url:
        print(f"Poster URL: {poster_url}")
    else:
        print("Movie not found.")
    return poster_url

# -------------- Routes ------------------
@app.route('/')
def index():
    start_time = time.time()  # Start timer for the entire function

    logs_by_user = {}

    if is_cache_valid():
        print("✅ Using cached data")
        cache = load_cache()
        logs_by_user = cache  # entire structure is now {username: [logs]}
    else:
        print("♻️ Recomputing cache")
        cache = {}

        def fetch_or_load_logs(username):
            print(f"⏳ Fetching diary for {username}")
            """
            Fetch the list of SLUGs from the Selected sheet.
            """
            selected_sheet = get_selected_sheet()
            selected_records = selected_sheet.get_all_records()
            selected_slugs = [row["SLUG"] for row in selected_records if "SLUG" in row]
            logs = get_all_user_logs(username, selected_slugs)
            return username, logs

        with concurrent.futures.ThreadPoolExecutor() as executor:
            user_sheet = get_users_sheet()
            usernames = [row[0] for row in user_sheet.get_all_values()[1:]]
            results = executor.map(fetch_or_load_logs, usernames)
            for username, logs in results:
                logs_by_user[username] = logs
                cache[username] = logs

        # Save updated cache
        save_cache(cache)

    end_time = time.time()  # End timer for the entire function
    print(f"✅ Total index() execution time: {end_time - start_time:.2f} seconds")

    return render_template('index.html', **build_stats(logs_by_user))

@app.route('/refresh/<username>', methods=['POST'])
def refresh_user(username):
    logs_by_user = {}
    """
    Fetch the list of SLUGs from the Selected sheet.
    """
    selected_sheet = get_selected_sheet()
    selected_records = selected_sheet.get_all_records()
    selected_slugs = [row["SLUG"] for row in selected_records if "SLUG" in row]
    for movie in selected_slugs:
        logs_by_user[(username, movie)] = get_all_user_logs(username, movie)

    cache = load_cache() if os.path.exists(CACHE_FILE) else {}
    for (u, m), logs in logs_by_user.items():
        cache[f"{u}||{m}"] = logs
    save_cache(cache)

    return redirect(url_for('index'))

@app.route('/parse-movie', methods=['POST'])
def parse_movie():
    link = request.form.get('url')
    if not link:
        return jsonify({"error": "Missing URL"}), 400

    full_url = expand_short_url(link)
    match = re.search(r'/film/([^/]+)/', full_url)
    if not match:
        return jsonify({"error": "Invalid Letterboxd link"}), 400

    slug = match.group(1)
    resp = requests.get(full_url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    title_tag = soup.find('meta', property='og:title')
    title = title_tag['content'] if title_tag else slug.replace('-', ' ').title()

    return jsonify({"title": title, "slug": slug, "url": full_url})

@app.route('/watchlist')
def watchlist():
    # Load the Watchlist and Selected sheets
    watchlist_sheet = get_watchlist_sheet()
    selected_sheet = get_selected_sheet()

    # Get all records from the Watchlist sheet
    watchlist_records = watchlist_sheet.get_all_records()

    # Get all records from the Selected sheet
    selected_records = selected_sheet.get_all_records()

    # Normalize boolean fields in the Watchlist
    for row in watchlist_records:
        row["IS_WATCHED"] = str(row.get("IS_WATCHED", "")).upper() == "TRUE"
        row["IS_NOMINATED"] = str(row.get("IS_NOMINATED", "")).upper() == "TRUE"
        row["IS_SELECTED"] = str(row.get("IS_SELECTED", "")).upper() == "TRUE"
        row["VOTED_BY"] = row.get("VOTED_BY", "").split(",") if row.get("VOTED_BY") else []

    # Normalize fields in the Selected sheet
    for row in selected_records:
        row["IS_WATCHED"] = True  # All movies in the Selected tab are considered watched
        row["WATCH_DATE"] = datetime.strptime(row.get("WATCHED_DATE", ""), '%m/%d/%Y') if row.get("WATCHED_DATE") else None

    # Find the movie in the Watchlist where IS_SELECTED = TRUE
    selected_movie = next((row for row in watchlist_records if row["IS_SELECTED"]), None)

    # Remove duplicates: Exclude movies from Watchlist that are already in Selected
    selected_slugs = {row["SLUG"] for row in selected_records}
    filtered_watchlist_records = [row for row in watchlist_records if row["SLUG"] not in selected_slugs]

    # Sort the Nominated records from the Watchlist
    sorted_nominated_records = sorted(
        [row for row in filtered_watchlist_records if row["IS_NOMINATED"]],
        key=lambda x: x["DATE_ADDED"]  # Sort by date added (optional)
    )

    # Sort the remaining records (not nominated and not watched)
    sorted_remaining_records = sorted(
        [row for row in filtered_watchlist_records if not row["IS_NOMINATED"] and not row["IS_WATCHED"] and not row["IS_SELECTED"]],
        key=lambda x: x["DATE_ADDED"]  # Sort by date added (optional)
    )

    # Sort the Watched records from the Selected table (oldest to most recent)
    sorted_watched_records = sorted(
        [row for row in selected_records if row["WATCH_DATE"]],
        key=lambda x: x["WATCH_DATE"]  # Sort by ascending order
    )

    # Combine all sorted records
    combined_records = []
    if selected_movie:
        combined_records.append(selected_movie)  # Add the selected movie first
    combined_records += sorted_nominated_records + sorted_remaining_records + sorted_watched_records

    # Load usernames from the Users sheet
    user_sheet = get_users_sheet()
    usernames = [row[0] for row in user_sheet.get_all_values()[1:]]

    return render_template("watchlist.html", movies=combined_records, usernames=usernames)

@app.route('/add-movie', methods=['POST'])
def add_movie():
    url = request.form.get('url')
    added_by = request.form.get('username')

    if not url or not added_by:
        return jsonify({"error": "Missing data"}), 400

    full_url = expand_short_url(url)
    match = re.search(r'/film/([^/]+)/', full_url)
    if not match:
        return jsonify({"error": "Invalid Letterboxd link"}), 400

    slug = match.group(1)

    try:
        resp = requests.get(full_url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Extract the data-tmdb-id attribute from the <body> tag
        body_tag = soup.find('body')
        tmdb_id = body_tag['data-tmdb-id'] if body_tag and 'data-tmdb-id' in body_tag.attrs else None
        print(tmdb_id)
        poster_url = get_poster(tmdb_id)  
        # Extract the movie title
        title_tag = soup.find('meta', property='og:title')
        title = title_tag['content'] if title_tag else slug.replace('-', ' ').title()

        # Regular expression to match the year in parentheses
        match = re.search(r'\((\d{4})\)', title)

        # Extract the year if a match is found
        year = match.group(1) if match else None

        # Remove the year from the title
        clean_title = re.sub(r'\s*\(\d{4}\)', '', title)

        # poster_url = get_poster(clean_title, year)   
        print(poster_url)    
        

    except Exception as e:
        return jsonify({"error": f"Error fetching movie data: {e}"}), 500

    date_added = datetime.now().strftime('%m/%d/%Y')

    sheet = get_watchlist_sheet()
    sheet.append_row([
        title,
        slug,
        full_url,
        added_by,
        date_added,
        poster_url,
        "FALSE",  # IS_WATCHED
        "FALSE"    # IS_NOMINATED
    ])

    return redirect(url_for('watchlist'))

@app.route('/delete_movie', methods=['POST'])
def delete_movie():
    movie_slug = request.form.get("slug")
    # Load your Google Sheets or database
    sheet = get_watchlist_sheet()  # Assuming `get_sheet()` is a function to get your Google Sheets or data source
    
    # Find the movie row by its slug
    movie_data = sheet.findall(movie_slug)
    
    if movie_data:
        # Assuming that the movie_slug uniquely identifies the movie, we delete it
        row = movie_data[0].row
        sheet.delete_rows(row)
    
    # Redirect back to the watchlist page
    return redirect(url_for('watchlist'))

@app.route('/mark-watched/<movie_slug>', methods=['POST'])
def mark_watched(movie_slug):
    # Load the Google Sheets
    watchlist_sheet = get_watchlist_sheet()
    nominated_sheet = get_nominations_sheet()
    selected_sheet = get_selected_sheet()

    # Get all records from the watchlist
    watchlist_records = watchlist_sheet.get_all_records()
    watchlist_headers = watchlist_sheet.row_values(1)

    # Find the movie row by its slug
    movie = next((row for row in watchlist_records if row["SLUG"] == movie_slug), None)

    if not movie:
        return jsonify({"error": "Movie not found in the watchlist"}), 404

    row_index = watchlist_records.index(movie) + 2  # Account for the header row

    # Check if the movie is selected
    if str(movie.get("IS_SELECTED", "")).upper() == "TRUE":
        # Step 1: Push all IS_NOMINATED movies to the Nominated table, except ignored slugs
        ignored_slugs = {"children-of-men", "rebecca", "dr-strangelove-or-how-i-learned-to-stop-worrying-and-love-the-bomb"}
        for idx, nominated_movie in enumerate(watchlist_records):
            if str(nominated_movie.get("IS_NOMINATED", "")).upper() == "TRUE":
                # Prepare the data for the nominated table
                nominated_data = [
                    nominated_movie["TITLE"],
                    nominated_movie["SLUG"],
                    nominated_movie["URL"],
                    nominated_movie["ADDED_BY"],
                    nominated_movie["DATE_ADDED"],
                    nominated_movie["POSTER"],
                    nominated_movie.get("NOMINATED_BY", ""),
                    nominated_movie.get("VOTED_BY", "")
                ]

                # Add the movie to the nominated table
                nominated_sheet.append_row(nominated_data)

                # Reset IS_NOMINATED and VOTED_BY in the watchlist table
                nominated_row_index = idx + 2  # Account for the header row
                watchlist_sheet.update_cell(nominated_row_index, watchlist_headers.index("IS_NOMINATED") + 1, "FALSE")
                watchlist_sheet.update_cell(nominated_row_index, watchlist_headers.index("VOTED_BY") + 1, "")
                watchlist_sheet.update_cell(nominated_row_index, watchlist_headers.index("IS_SELECTED") + 1, "")
                watchlist_sheet.update_cell(nominated_row_index, watchlist_headers.index("NOMINATED_BY") + 1, "")
                watchlist_sheet.update_cell(nominated_row_index, watchlist_headers.index("VOTED_BY") + 1, "")

        # Step 2: Push the IS_SELECTED movie to the Selected table
        selected_data = [
            movie["TITLE"],
            movie["SLUG"],
            movie["URL"],
            movie["ADDED_BY"],
            movie["DATE_ADDED"],
            movie["POSTER"],
            movie.get("NOMINATED_BY", ""),
            movie.get("VOTED_BY", ""),
            datetime.now().strftime('%m/%d/%Y')  # WATCHED_DATE
        ]

        # Add the movie to the selected table
        selected_sheet.append_row(selected_data)

        # Reset IS_SELECTED in the watchlist table
        watchlist_sheet.update_cell(row_index, watchlist_headers.index("IS_SELECTED") + 1, "")

    # Step 3: Mark the movie as watched (IS_WATCHED = TRUE)
    is_watched_col = watchlist_headers.index("IS_WATCHED") + 1  # Find the column for IS_WATCHED
    watchlist_sheet.update_cell(row_index, is_watched_col, "TRUE")  # Update the cell to TRUE

    # Reset IS_SELECTED, IS_NOMINATED, NOMINATED_BY, and VOTED_BY in the watchlist table
    watchlist_sheet.update_cell(row_index, watchlist_headers.index("IS_SELECTED") + 1, "")
    watchlist_sheet.update_cell(row_index, watchlist_headers.index("IS_NOMINATED") + 1, "")
    watchlist_sheet.update_cell(row_index, watchlist_headers.index("NOMINATED_BY") + 1, "")
    watchlist_sheet.update_cell(row_index, watchlist_headers.index("VOTED_BY") + 1, "")

    return redirect(url_for('watchlist'))

@app.route('/mark-unwatched/<movie_slug>', methods=['POST'])
def mark_unwatched(movie_slug):
    # Load the Google Sheet
    sheet = get_watchlist_sheet()

    # Find the movie row by its slug
    movie_data = sheet.findall(movie_slug)

    if movie_data:
        # Assuming the movie_slug uniquely identifies the movie, update the IS_WATCHED column
        row = movie_data[0].row
        is_watched_col = sheet.find("IS_WATCHED").col  # Find the column for IS_WATCHED
        sheet.update_cell(row, is_watched_col, "FALSE")  # Update the cell to FALSE

    # Redirect back to the watchlist page
    return redirect(url_for('watchlist'))

@app.route('/nominate', methods=['POST'])
def nominate_movie():
    slug = request.form.get("slug")
    username = request.form.get("username")

    sheet = get_watchlist_sheet()
    records = sheet.get_all_records()
    headers = sheet.row_values(1)

    for idx, row in enumerate(records):
        if row["SLUG"] == slug:
            row_index = idx + 2  # header is row 1
            sheet.update_cell(row_index, headers.index("IS_NOMINATED") + 1, "TRUE")
            sheet.update_cell(row_index, headers.index("NOMINATED_BY") + 1, username)
            break

    return redirect(url_for("watchlist"))

@app.route('/remove_nomination', methods=['POST'])
def remove_nomination():
    slug = request.form.get("slug")

    sheet = get_watchlist_sheet()
    records = sheet.get_all_records()
    headers = sheet.row_values(1)

    for idx, row in enumerate(records):
        if row["SLUG"] == slug:
            row_index = idx + 2
            sheet.update_cell(row_index, headers.index("IS_NOMINATED") + 1, "FALSE")
            sheet.update_cell(row_index, headers.index("NOMINATED_BY") + 1, "")
            sheet.update_cell(row_index, headers.index("VOTED_BY") + 1, "")
            break

    return redirect(url_for("watchlist"))

@app.route('/vote_movie', methods=['POST'])
def vote_movie():
    slug = request.form.get("slug")
    username = request.form.get("username")  # Get the username from the dropdown

    if not username:
        return redirect(url_for("watchlist"))  # Redirect if no username is provided

    sheet = get_watchlist_sheet()
    records = sheet.get_all_records()
    headers = sheet.row_values(1)

    for idx, row in enumerate(records):
        if row["SLUG"] == slug:
            row_index = idx + 2  # Row index in Google Sheets (1-based index)
            voted_by = row.get("VOTED_BY", "")
            
            # Split the current voted_by list into a list of users and strip whitespace
            voted_by_list = [user.strip() for user in voted_by.split(",")] if voted_by else []
            
            if username.strip() in voted_by_list:
                # If the user has already voted, remove their vote
                voted_by_list.remove(username.strip())
            else:
                # If the user hasn't voted, add their vote
                voted_by_list.append(username.strip())
            
            # Update the VOTED_BY field
            new_voted_by = ", ".join(voted_by_list)
            sheet.update_cell(row_index, headers.index("VOTED_BY") + 1, new_voted_by)
            break

    return redirect(url_for("watchlist"))

@app.route('/winning_movie', methods=['POST'])
def winning_movie():
    slug = request.form.get("slug")

    # Get the watchlist, nominated, and selected sheets
    # watchlist_sheet = get_watchlist_sheet()
    # nominated_sheet = get_nominations_sheet()
    # selected_sheet = get_selected_sheet()

    # # Get all records from the watchlist
    # watchlist_records = watchlist_sheet.get_all_records()
    # watchlist_headers = watchlist_sheet.row_values(1)

    # # Step 1: Find the movie in the watchlist by its slug
    # movie = next((row for row in watchlist_records if row["SLUG"] == slug), None)

    # if not movie:
    #     return jsonify({"error": "Movie not found in the watchlist"}), 404

    # # Prepare the data for the selected table
    # selected_data = [
    #     movie["TITLE"],
    #     movie["SLUG"],
    #     movie["URL"],
    #     movie["ADDED_BY"],
    #     movie["DATE_ADDED"],
    #     movie["POSTER"],
    #     movie.get("NOMINATED_BY", ""),
    #     movie.get("VOTED_BY", ""),
    #     datetime.now().strftime('%m/%d/%Y')  # WATCHED_DATE
    # ]

    # # Add the movie to the selected table
    # selected_sheet.append_row(selected_data)

    # # Step 2: Update the IS_SELECTED cell in the watchlist table to TRUE
    # row_index = watchlist_records.index(movie) + 2  # Account for the header row
    # watchlist_sheet.update_cell(row_index, watchlist_headers.index("IS_SELECTED") + 1, "TRUE")

    # # Step 3: Find all nominated movies in the watchlist and add them to the nominated table
    # nominated_movies = [row for row in watchlist_records if row.get("IS_NOMINATED", "").upper() == "TRUE"]

    # for nominated_movie in nominated_movies:
    #     # Prepare the data for the nominated table
    #     nominated_data = [
    #         nominated_movie["TITLE"],
    #         nominated_movie["SLUG"],
    #         nominated_movie["URL"],
    #         nominated_movie["ADDED_BY"],
    #         nominated_movie["DATE_ADDED"],
    #         nominated_movie["POSTER"],
    #         nominated_movie.get("NOMINATED_BY", ""),
    #         nominated_movie.get("VOTED_BY", "")
    #     ]

    #     # Add the movie to the nominated table
    #     nominated_sheet.append_row(nominated_data)

    #     # Reset the IS_NOMINATED flag and clear VOTED_BY in the watchlist table
    #     row_index = watchlist_records.index(nominated_movie) + 2  # Account for the header row
    #     watchlist_sheet.update_cell(row_index, watchlist_headers.index("IS_NOMINATED") + 1, "FALSE")
    #     watchlist_sheet.update_cell(row_index, watchlist_headers.index("VOTED_BY") + 1, "")

    # return redirect(url_for("watchlist"))
    # Get the watchlist sheet
    watchlist_sheet = get_watchlist_sheet()

    # Get all records from the watchlist
    watchlist_records = watchlist_sheet.get_all_records()
    watchlist_headers = watchlist_sheet.row_values(1)

    # Step 1: Find the movie in the watchlist by its slug
    movie = next((row for row in watchlist_records if row["SLUG"] == slug), None)

    if not movie:
        return jsonify({"error": "Movie not found in the watchlist"}), 404

    # Step 2: Update the IS_NOMINATED flag to FALSE and IS_SELECTED flag to TRUE
    row_index = watchlist_records.index(movie) + 2  # Account for the header row
    watchlist_sheet.update_cell(row_index, watchlist_headers.index("IS_NOMINATED") + 1, "FALSE")
    watchlist_sheet.update_cell(row_index, watchlist_headers.index("IS_SELECTED") + 1, "TRUE")

    return redirect(url_for("watchlist"))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)