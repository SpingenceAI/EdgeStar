# Gmail Setup

Follow the steps below to setup gmail credentials
[Reference](https://developers.google.com/gmail/api/quickstart/python)

## Step 1: Create a gmail account
## Step 2: Go to [Google Cloud Console](https://console.cloud.google.com/)
![image](./images/google_console.png)

## Step 3: Create a new project
![image](./images/create_project.png)
![image](./images/create_project_2.png)

## Step 4: Enable Gmail API
![image](./images/enable_gmail_api.png)
![image](./images/enable_gmail_api_2.png)

## Step 5: Setup OAuth 2.0
![image](./images/setup_oauth.png)
![image](./images/setup_oauth_2.png)
![image](./images/setup_oauth_3.png)

## Step 6: Setup credentials
![image](./images/create_credentials.png)
![image](./images/download_credentials.png)

## Step 7: install library
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

## Step 8: Login to setup credentials on device
[quickstart.py](./quickstart.py)
![image](./images/setup_credentials.png)
Able to access gmail folders
![image](./images/gmail_folders.png)