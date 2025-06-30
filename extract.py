import json
import requests
import time

# Configuration
URL = "https://api-inbox.chatbotize.com/graphql"
TOKEN = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJjaGF0Ym90aXplIiwic3ViIjoiMmEwNzUwZjdlYTdkNDQwMGIzZWEyZDkxMmI3OTU5OGMiLCJhdWQiOlsiY2hhdGJvdGl6ZSJdLCJleHAiOjE3NTM4ODc1NDEsImlhdCI6MTc1MTI5NTU0MSwianRpIjoiYWJlMmExMjNkYzEyNGZlMzkzYjViZDYzMTczYzAzZmE2OWI0MjgxZDk1ZGY0OWM4ODAyMmNlNjQ4NmY5YTI3YSJ9.PGLFPIMhevYp4NobRj1xm92aGdiF4ao4Yn0U4EHW4hGv-Uj-eGye97MGUvbc3nLlrTPsIAAZLvGwPNoBtfs_Zw-HP5GTJHFqNCbSUwxXcVSP1Fc-mE9cDyHWR8R_Dqghs8DWBnUQfVak33UMeLolFDwhZQJFFjP5-h7rADnPwfMtfLumGGhB_kZXGI7NSQqa0OEvTl0g8vGUjO9tz16WHvnnClk9VncUGhf269FzrxgfhrdFdYXfLmcl0ll7WscZ5UecMBo_imlmgdb2O2vSPxqCvDka0EL8LJPf5GegCegvtjQW3NltMM4cKL0NlLhIK69G7MLpxlQ2w8GKxw96gQ"
ENV_ID = "f8cab5ef2ba74c3c92bee8dc75d15e53"
HEADERS = {
    "Authorization": TOKEN,
    "Content-Type": "application/json",
    "Origin": "https://app.zowie.ai",
    "Referer": "https://app.zowie.ai/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36"
}

# Storage for all fetched conversations
all_conversations = []

# Build payload with fuzzed page value

def build_payload(page):
    return {
        "operationName": "SearchConversations",
        "variables": {
            "environmentId": ENV_ID,
            "page": page,
            "sortBy": "START_TIME",
            "sortDirection": "DESC",
            "channelIdsFilter": ["email"],
            "entriesPerPage": 100,
            "agentIdsFilter": [],
            "departmentIdsFilter": []
        },
        "query": """
            query SearchConversations($page: Int!, $entriesPerPage: Int!, $environmentId: String!, $sortBy: ConversationsSortBy, $sortDirection: ConversationSortDirection, $textFilter: String, $clientFilter: String, $ticketIdFilter: String, $startFromFilter: Long, $startToFilter: Long, $lastMessageTimeFromFilter: Long, $lastMessageTimeToFilter: Long, $channelIdsFilter: [String!]!, $agentIdsFilter: [String!]!, $departmentIdsFilter: [String!]!, $quickFilter: String) {
              searchConversations(page: $page, entriesPerPage: $entriesPerPage, environmentId: $environmentId, sortBy: $sortBy, sortDirection: $sortDirection, textFilter: $textFilter, clientFilter: $clientFilter, ticketIdFilter: $ticketIdFilter, startFromFilter: $startFromFilter, startToFilter: $startToFilter, lastMessageTimeFromFilter: $lastMessageTimeFromFilter, lastMessageTimeToFilter: $lastMessageTimeToFilter, channelIdsFilter: $channelIdsFilter, agentIdsFilter: $agentIdsFilter, departmentIdsFilter: $departmentIdsFilter, quickFilter: $quickFilter) {
                conversationId
              }
            }
        """
    }

# Main fuzzing loop: replace FUZZ with numbers 1 to 1,000,000
for page in range(1, 1_000_001):
    print(f"Sending request with page={page}")
    payload = build_payload(page)
    response = requests.post(URL, headers=HEADERS, json=payload)

    if response.status_code == 200:
        try:
            data = response.json()
            conversations = data.get("data", {}).get("searchConversations", [])
            for conv in conversations:
                cid = conv.get("conversationId")
                if cid:
                    all_conversations.append(cid)
                    print(f"Found conversationId: {cid}")
            # Save after each page
            with open("conv.json", "w") as f:
                json.dump(all_conversations, f, indent=2)
        except Exception as e:
            print(f"Error parsing response on page {page}: {e}")
    else:
        print(f"Request failed at page {page}: {response.status_code}")

    time.sleep(0.1)
