import gspread
from oauth2client.service_account import ServiceAccountCredentials

import gspread
from oauth2client.service_account import ServiceAccountCredentials

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

users_sheet = get_users_sheet()

# Get all rows as list of dicts (headers used as keys)
users_data = users_sheet.get_all_records()
print(users_data)

# Or just raw cell values
all_values = users_sheet.get_all_values()
