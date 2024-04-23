from flask import Flask, request, redirect, jsonify
import requests
from urllib.parse import urlencode, urlparse, parse_qs

app = Flask(__name__)

# LinkedIn API Keys and Endpoints
client_id = "YOUR-CLIENT-ID"
client_secret = "YOUR-CLIENT-SECRET"
redirect_uri = "http://localhost:5000/callback"
auth_url = "https://www.linkedin.com/oauth/v2/authorization"
token_url = "https://www.linkedin.com/oauth/v2/accessToken"

@app.route("/")
def index():
    # Define your client ID, callback URL, and scopes
    callback_url = "http://localhost:5000/callback"
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': callback_url,
        'scope': 'openid profile email w_member_social'
    }
    authorization_url = auth_url + "?" + urlencode(params)
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    authorization_code = request.args.get('code')
    token_params = {
        'grant_type': 'authorization_code',
        'code': authorization_code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri
    }
    response = requests.post(token_url, data=token_params)
    if response.status_code == 200:
        response_data = response.json()
        if 'access_token' in response_data:
            access_token = response_data['access_token']
            profile_url = "https://api.linkedin.com/v2/userinfo"
            headers = {'Authorization': f'Bearer {access_token}'}
            profile_response = requests.get(profile_url, headers=headers)
            profile_data = profile_response.json()
            return jsonify(profile_data)
    return "Error occurred"

if __name__ == "__main__":
    app.run(debug=True)
