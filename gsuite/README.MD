## Prerequisites:

- Create a new Google Cloud project

- Enable the Google Drive API, Gmail API, 
- Maps API (May need a set-up a billing account), 
    - Enabled all APIs, Restrict requests to localhost if you want (for testing)
    - Get started here: https://developers.google.com/maps/documentation/places/web-service/get-api-key

- Configure an OAuth consent screen

- Add OAuth scopes
    - https://www.googleapis.com/auth/drive.readonly
    - https://www.googleapis.com/auth/gmail.modify
    - https://www.googleapis.com/auth/userinfo.email
    - https://www.googleapis.com/auth/userinfo.profile

- Create an OAuth Client ID for application type "Web application"

- Download the JSON file of your client's OAuth keys

- Rename the key file to gcp-oauth.keys.json and place into the root of this repo (i.e. credentials/gcp-oauth.keys.json)


## Common issues
- Unable to sign-in, getting Access Denied error: Add Test Users to your GCP Project
- Not receiving refresh_token as part of your credentials. Check out [this Stackoverflow page](https://stackoverflow.com/questions/38467374/google-api-refresh-token-null-and-how-to-refresh-access-token/41105959#41105959)


## Next steps (DIY) :

- Write a function to re-authenticate (to allow account switching)
- Explain the list_files function to enhance search functionalities using more [query parameters](https://developers.google.com/workspace/drive/api/guides/ref-search-terms)

- Refresh token automatically
- Avoid re-building client for every function call

# Sample prompts
- What is the distance between Connaught Place New Delhi and Khan Market?
- Give me directions from Connaught Place New Delhi and Khan Market?
- Give me restaurants in Khan Market New Delhi