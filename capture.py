import json
from urllib.parse import urlparse

def parse_har_and_search_string(har_file, search_string=None, content_type_filter=None, method_filter=None, content_type_location="both"):
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

        # List to store matching entries
        results = []

        for idx, entry in enumerate(entries):
            request = entry.get('request', {})
            response = entry.get('response', {})
            url = request.get('url', '')
            method = request.get('method', 'UNKNOWN')

            # **Only consider selected method (POST or GET)**
            if method_filter and method.upper() != method_filter.upper():
                continue  # Skip if the method does not match the filter

            # Extract headers, post data, and content from request and response
            headers = request.get('headers', [])
            response_headers = response.get('headers', [])
            request_post_data = request.get('postData', {}).get('text', '')
            response_content = response.get('content', {}).get('text', '')
            
            # Extract content type from headers (request and response)
            content_type_request = 'UNKNOWN'
            content_type_response = 'UNKNOWN'

            # Iterate over request headers to find Content-Type
            for header in headers:
                if header.get('name', '').lower() == 'content-type':
                    content_type_request = header.get('value', 'UNKNOWN')
                    break

            # Iterate over response headers to find Content-Type
            for header in response_headers:
                if header.get('name', '').lower() == 'content-type':
                    content_type_response = header.get('value', 'UNKNOWN')
                    break

            # Parse URL to check for matches in query parameters
            parsed_url = urlparse(url)
            query = parsed_url.query
            domain = parsed_url.netloc

            # Skip requests to ad-related domains
            if any(ad_domain in domain for ad_domain in ad_domains):
                continue

            # Ensure content_type_request and content_type_response are never None
            content_type_request = content_type_request or ''
            content_type_response = content_type_response or ''

            # Only consider transactions with the specified content type filter
            content_type_match = False
            if content_type_location == "request" and content_type_filter and content_type_filter in content_type_request:
                content_type_match = True
            elif content_type_location == "response" and content_type_filter and content_type_filter in content_type_response:
                content_type_match = True
            elif content_type_location == "both" and content_type_filter:
                # Ensure content_type_filter is checked against non-None content types
                if content_type_filter in content_type_request or content_type_filter in content_type_response:
                    content_type_match = True

            # Check for search_string matches in the request and response
            match_found = False
            if search_string:
                # Check in query parameters
                if search_string in query:
                    match_found = True
                # Check in headers
                if any(search_string in header.get('name', '') or search_string in header.get('value', '') for header in headers):
                    match_found = True
                # Check in request body (POST data)
                if search_string in request_post_data:
                    match_found = True
                # Check in response content
                if search_string in response_content:
                    match_found = True

            # If no matches for the search string, but a content-type filter is applied and matches, include it
            if (search_string and match_found) or (not search_string and content_type_match):
                # Append matching transaction details
                status = response.get('status', None)
                started_date_time = entry.get('startedDateTime', 'UNKNOWN')
                time_taken = entry.get('time', 'UNKNOWN')

                results.append({
                    "Packet Number": idx + 1,
                    "URL": url,
                    "Method": method,
                    "Status": status,
                    "Start Time": started_date_time,
                    "Time Taken (ms)": time_taken,
                    "Transaction Type": content_type_response
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

        # Ask for content type location (request, response, or both)
        content_type_location = input("Enter where to search for content-type (request/response/both): ").strip().lower()
        if content_type_location not in ['request', 'response', 'both']:
            print("Invalid content type location. Please enter 'request', 'response', or 'both'.")
            continue

        # Parse the HAR file and search for the string
        results = parse_har_and_search_string(har_path, search_string, content_type_filter, method_filter, content_type_location)
        
        if isinstance(results, list) and results:
            for result in results:
                print("Match Found:")
                for key, value in result.items():
                    print(f"{key}: {value}")
                print("\n")
        else:
            print("No matching transactions found.")