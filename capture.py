import json
from urllib.parse import urlparse

def parse_har_and_search_string(har_file, search_string=None, content_type_filter=None, method_filter=None):
    try:
        # Open and load the HAR file
        with open(har_file, 'r', encoding='utf-8') as file:
            har_data = json.load(file)

        # Verify the structure of HAR file
        if 'log' not in har_data or 'entries' not in har_data['log']:
            return "Invalid HAR file structure"

        entries = har_data['log']['entries']

        # Define a list of ad-related domains to exclude
        ad_domains = [
            "doubleclick.net",
            "googleads.g.doubleclick.net",
            "googleadservices.com",
            "googlesyndication.com",
            "google-analytics.com",
            "ads.linkedin.com",
            "facebook.com",
            "twitter.com"
        ]

        # Search for the string in the entire request and response
        results = []
        for idx, entry in enumerate(entries):
            request = entry.get('request', {})
            response = entry.get('response', {})
            url = request.get('url', '')
            method = request.get('method', 'UNKNOWN')

            # Debug: Print method and URL to check
            print(f"Processing entry #{idx + 1}, Method: {method}, URL: {url}")

            # **Only consider selected method (POST or GET)**
            if method_filter:
                if method.upper() != method_filter.upper():
                    continue  # Skip if the method does not match the filter

            headers = request.get('headers', [])
            response_headers = response.get('headers', [])
            request_post_data = request.get('postData', {}).get('text', '')
            response_content = response.get('content', {}).get('text', '')
            content_type = response.get('content', {}).get('mimeType', 'UNKNOWN')

            # Extract content type from both request and response headers
            for header in headers + response_headers:
                if header.get('name', '').lower() == 'content-type':
                    content_type = header.get('value', '')
                    break

            # Debug: Check content type
            print(f"Content Type: {content_type}, Content Type Filter: {content_type_filter}")

            # Parse URL to check for matches in query parameters
            parsed_url = urlparse(url)
            query = parsed_url.query
            domain = parsed_url.netloc

            # Skip requests to ad-related domains
            if any(ad_domain in domain for ad_domain in ad_domains):
                continue

            # Only consider transactions with the specified content type filter
            if content_type_filter and content_type_filter not in content_type:
                print(f"Skipping entry due to content type mismatch: {content_type}")
                continue  # Skip this transaction if content type does not match the filter

            # Check for matches in the request and response
            match_sources = []

            if search_string and search_string in query:
                match_sources.append("Request Query Parameter")
            if search_string and any(search_string in header.get('name', '') or search_string in header.get('value', '') for header in headers):
                match_sources.append("Request Header")
            if search_string and search_string in request_post_data:
                match_sources.append("Request Body")
            if search_string and search_string in response_content:
                match_sources.append("Response Content")

            # Debug: Check if any matches were found
            print(f"Match Sources: {match_sources}")

            # Append matching transaction details
            status = response.get('status', None)
            started_date_time = entry.get('startedDateTime', 'UNKNOWN')
            time_taken = entry.get('time', 'UNKNOWN')

            # If there are any matches or if the content type matches the filter, include the entry
            if match_sources or (not search_string and content_type_filter):
                results.append({
                    "Packet Number": idx + 1,
                    "URL": url,
                    "Method": method,
                    "Status": status,
                    "Start Time": started_date_time,
                    "Time Taken (ms)": time_taken,
                    "Match Sources": ", ".join(match_sources) if match_sources else "Content Type Filter",
                    "Transaction Type": content_type
                })

        # Return results or a message if no matches are found
        return results if results else "No matching transactions found."

    except FileNotFoundError:
        return f"Error: File '{har_file}' not found."
    except json.JSONDecodeError:
        return "Error: Failed to parse HAR file. Make sure it is a valid JSON."

if __name__ == "__main__":
    while True:
        # Input HAR file path and search string
        har_file = input("Enter the HAR file path (or 'q' to quit): ").strip()
        if har_file.lower() == 'q':
            break
        har_path = "/Users/aluo/Desktop/har_files/" + har_file + ".har"
        
        # Ask for the method filter (POST, GET, or None)
        method_filter = input("Enter HTTP method to filter (POST/GET), or leave blank to search all methods: ").strip()
        
        # Validate method filter input
        if method_filter.lower() not in ['post', 'get', '']:
            print("Invalid method. Please enter POST, GET, or leave blank for no filter.")
            continue

        # Ask for the search string
        search_string = input("Enter the search string (leave blank to filter by content type only): ").strip()
        
        # Ask for content type filter
        content_type_filter = input("Enter content type to filter (e.g., image/jpeg, application/json) or leave blank to skip: ").strip()
        content_type_filter = content_type_filter if content_type_filter else None

        # Parse the HAR file and search for the string
        results = parse_har_and_search_string(har_path, search_string, content_type_filter, method_filter)
        
        if isinstance(results, list) and results:
            for result in results:
                print("Match Found:")
                for key, value in result.items():
                    print(f"{key}: {value}")
                print("\n")
        else:
            print("No matching transactions found.")
