import gspread
from oauth2client.service_account import ServiceAccountCredentials
from cache import is_cache_valid, load_cache, save_cache, CACHE_FILE, flush_cache
import os

def get_users_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "onlycinephiles-b6b986d3cb57.json", scope
    )
    client = gspread.authorize(creds)
    
    # Open the spreadsheet
    spreadsheet = client.open("OnlyCinephilesDB")
    
    # Access the specific sheet (tab) called "Users"
    return spreadsheet.worksheet("Users")

def get_watchlist_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "onlycinephiles-b6b986d3cb57.json", scope
    )
    client = gspread.authorize(creds)
    
    # Open the spreadsheet
    spreadsheet = client.open("OnlyCinephilesDB")
    
    # Access the specific sheet (tab) called "Users"
    return spreadsheet.worksheet("Watchlist")

def get_nominations_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "onlycinephiles-b6b986d3cb57.json", scope
    )
    client = gspread.authorize(creds)
    
    # Open the spreadsheet
    spreadsheet = client.open("OnlyCinephilesDB")
    
    # Access the specific sheet (tab) called "Users"
    return spreadsheet.worksheet("Nominations")

def get_selected_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "onlycinephiles-b6b986d3cb57.json", scope
    )
    client = gspread.authorize(creds)
    
    # Open the spreadsheet
    spreadsheet = client.open("OnlyCinephilesDB")
    
    # Access the specific sheet (tab) called "Users"
    return spreadsheet.worksheet("Selected")

def get_selected_records():
    cache = load_cache() if os.path.exists(CACHE_FILE) else {}
    selected_records = cache.get("selected_records")
    if selected_records:
        print("✅ Using selected records from cache")
        return selected_records
    else:
        print("♻️ Fetching selected records from sheet and updating cache")
        selected_sheet = get_selected_sheet()
        selected_records = selected_sheet.get_all_records()
        cache["selected_records"] = selected_records
        save_cache(cache)
        return selected_records

def get_meetings_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "onlycinephiles-b6b986d3cb57.json", scope
    )
    client = gspread.authorize(creds)
    
    # Open the spreadsheet
    spreadsheet = client.open("OnlyCinephilesDB")
    
    # Access the specific sheet (tab) called "Users"
    return spreadsheet.worksheet("Meetings")

def get_meetings_records():
    cache = load_cache() if os.path.exists(CACHE_FILE) else {}
    meetings_records = cache.get("meetings_records")
    if meetings_records:
        print("✅ Using meetings records from cache")
        return meetings_records
    else:
        print("♻️ Fetching meetings records from sheet and updating cache")
        meetings_sheet = get_meetings_sheet()
        meetings_records = meetings_sheet.get_all_records()
        cache["meetings_records"] = meetings_records
        save_cache(cache)
        return meetings_records
# users_sheet = get_users_sheet()

# # Get all rows as list of dicts (headers used as keys)
# users_data = users_sheet.get_all_records()
# print(users_data)

# # Or just raw cell values
# all_values = users_sheet.get_all_values()
