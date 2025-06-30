import requests
import json
import concurrent.futures
import time

# --- Configuration ---
BASE_URL = "https://api-inbox.chatbotize.com/graphql"
AUTH_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJjaGF0Ym90aXplIiwic3ViIjoiMmEwNzUwZjdlYTdkNDQwMGIzZWEyZDkxMmI3OTU5OGMiLCJhdWQiOlsiY2hhdGJvdGl6ZSJdLCJleHAiOjE3NTM4ODc1NDEsImlhdCI6MTc1MTI5NTU0MSwianRpIjoiYWJlMmExMjNkYzEyNGZlMzkzYjViZDYzMTczYzAzZmE2OWI0MjgxZDk1ZGY0OWM4ODAyMmNlNjQ4NmY5YTI3YSJ9.PGLFPIMhevYp4NobRj1xm92aGdiF4ao4Yn0U4EHW4hGv-Uj-eGye97MGUvbc3nLlrTPsIAAZLvGwPNoBtfs_Zw-HP5GTJHFqNCbSUwxXcVSP1Fc-mE9cDyHWR8R_Dqghs8DWBnUQfVak33UMeLolFDwhZQJFFjP5-h7rADnPwfMtfLumGGhB_kZXGI7NSQqa0OEvTl0g8vGUjO9tz16WHvnnClk9VncUGhf269FzrxgfhrdFdYXfLmcl0ll7WscZ5UecMBo_imlmgdb2O2vSPxqCvDka0EL8LJPf5GegCegvtjQW3NltMM4cKL0NlLhIK69G7MLpxlQ2w8GKxw96gQ"
MAX_PAGES = 1000000  # As requested, 1 to 1,000,000
ENTRIES_PER_PAGE = 100
MAX_WORKERS = 20  # Number of concurrent threads

# --- Headers and Query Template ---
HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "*/*",
    "Sec-Ch-Ua-Platform": "\"Linux\"",
    "Sec-Ch-Ua": "\"Not?A_Brand\";v=\"99\", \"Chromium\";v=\"130\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36",
    "Origin": "https://app.zowie.ai",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://app.zowie.ai/",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Priority": "u=1, i" # Note: some systems might not allow setting Priority header directly
}

QUERY_TEMPLATE = {
    "operationName": "SearchConversations",
    "variables": {
        "environmentId": "f8cab5ef2ba74c3c92bee8dc75d15e53",
        "page": "FUZZ",  # This will be replaced
        "sortBy": "START_TIME",
        "sortDirection": "DESC",
        "channelIdsFilter": ["email"],
        "entriesPerPage": ENTRIES_PER_PAGE,
        "agentIdsFilter": [],
        "departmentIdsFilter": []
    },
    "query": "query SearchConversations($page: Int!, $entriesPerPage: Int!, $environmentId: String!, $sortBy: ConversationsSortBy, $sortDirection: ConversationSortDirection, $textFilter: String, $clientFilter: String, $ticketIdFilter: String, $startFromFilter: Long, $startToFilter: Long, $lastMessageTimeFromFilter: Long, $lastMessageTimeToFilter: Long, $channelIdsFilter: [String!]!, $agentIdsFilter: [String!]!, $departmentIdsFilter: [String!]!, $quickFilter: String) {\n  searchConversations(page: $page, entriesPerPage: $entriesPerPage, environmentId: $environmentId, sortBy: $sortBy, sortDirection: $sortDirection, textFilter: $textFilter, clientFilter: $clientFilter, ticketIdFilter: $ticketIdFilter, startFromFilter: $startFromFilter, startToFilter: $startToFilter, lastMessageTimeFromFilter: $lastMessageTimeFromFilter, lastMessageTimeToFilter: $lastMessageTimeToFilter, channelIdsFilter: $channelIdsFilter, agentIdsFilter: $agentIdsFilter, departmentIdsFilter: $departmentIdsFilter, quickFilter: $quickFilter) {\n    conversationId\n    channelId\n    title\n    contact {\n      firstName\n      lastName\n      name\n      email\n      __typename\n    }\n    ticketId\n    startTime\n    lastMessageTime\n    messagesCount\n    agentIds {\n      agentId\n      firstName\n      lastName\n      email\n      __typename\n    }\n    departments {\n      id\n      name\n      __typename\n    }\n    __typename\n  }\n}\n"
}

def send_request(page_number):
    """
    Sends a POST request to the GraphQL endpoint for a specific page.
    Extracts and returns conversationIds.
    """
    payload = json.loads(json.dumps(QUERY_TEMPLATE)) # Deep copy
    payload["variables"]["page"] = page_number

    try:
        response = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        data = response.json()
        conversation_ids = []

        if "data" in data and data["data"] and "searchConversations" in data["data"] and data["data"]["searchConversations"]:
            for conv in data["data"]["searchConversations"]:
                if "conversationId" in conv:
                    conversation_ids.append(conv["conversationId"])

            print(f"Page {page_number}: Found {len(conversation_ids)} conversationIds.")
            if not conversation_ids and ENTRIES_PER_PAGE > 0 : # if we expect results but get none, it might be the end
                 # This could be a heuristic to stop if a page returns no results,
                 # assuming subsequent pages will also be empty.
                 # For now, we'll let it run up to MAX_PAGES as requested.
                 pass

        elif "errors" in data:
            print(f"Page {page_number}: Received GraphQL errors: {data['errors']}")
        else:
            print(f"Page {page_number}: No conversation data found or unexpected response structure.")

        return conversation_ids

    except requests.exceptions.Timeout:
        print(f"Page {page_number}: Request timed out.")
    except requests.exceptions.HTTPError as e:
        print(f"Page {page_number}: HTTP error: {e.response.status_code} - {e.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Page {page_number}: Request failed: {e}")
    except json.JSONDecodeError:
        print(f"Page {page_number}: Failed to decode JSON response.")

    return [] # Return empty list on error

if __name__ == "__main__":
    all_conversation_ids = []
    start_time = time.time()

    # For testing with a smaller range first:
    # test_max_pages = 50
    # print(f"Starting to fetch conversations for pages 1 to {test_max_pages} with {MAX_WORKERS} workers...")

    print(f"Starting to fetch conversations for pages 1 to {MAX_PAGES} with {MAX_WORKERS} workers...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # future_to_page = {executor.submit(send_request, page): page for page in range(1, test_max_pages + 1)} # For testing
        future_to_page = {executor.submit(send_request, page): page for page in range(1, MAX_PAGES + 1)}

        for future in concurrent.futures.as_completed(future_to_page):
            page = future_to_page[future]
            try:
                result_ids = future.result()
                if result_ids:
                    all_conversation_ids.extend(result_ids)
            except Exception as exc:
                print(f"Page {page} generated an exception: {exc}")

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n--- Summary ---")
    print(f"Finished fetching data.")
    print(f"Total conversationIds collected: {len(all_conversation_ids)}")
    print(f"Total unique conversationIds collected: {len(set(all_conversation_ids))}")
    print(f"Total time taken: {total_time:.2f} seconds")

    # Optionally, save all_conversation_ids to a file
    # with open("conversation_ids.txt", "w") as f:
    #     for conv_id in set(all_conversation_ids): # Save unique IDs
    #         f.write(f"{conv_id}\n")
    # print("Unique conversation IDs saved to conversation_ids.txt")
