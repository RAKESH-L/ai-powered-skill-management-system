import requests
import json

def fetch_github_details(username, access_token):
    # Fetch user details
    url = f"https://api.github.com/users/{username}"
    headers = {
        'Authorization': f'token {access_token}'
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        user_data = response.json()
        # Extracting required user details
        required_user_details = {
            'login': user_data['login'],
            'id': user_data['id'],
            'node_id': user_data['node_id'],
            'avatar_url': user_data['avatar_url'],
            'blog': user_data.get('blog', None),
            'email': user_data.get('email', None),
            'bio': user_data.get('bio', None),
            'public_repos': user_data['public_repos'],
            'public_gists': user_data['public_gists'],
            'followers': user_data['followers'],
            'following': user_data['following'],
            'created_at': user_data['created_at'],
            'updated_at': user_data['updated_at']
        }
    else:
        print(f"Failed to fetch GitHub details. Status code: {response.status_code}")
        return None

    # Fetch repositories
    repos_url = f"https://api.github.com/users/{username}/repos"
    response = requests.get(repos_url, headers=headers)

    if response.status_code == 200:
        repos_data = response.json()
    else:
        print(f"Failed to fetch GitHub repositories. Status code: {response.status_code}")
        return None

    # Process repositories
    languages_usage = {}
    notebook_count = 0
    total_repos = len(repos_data)
    repositories = []
    for repo in repos_data:
        repo_languages_url = repo['languages_url']
        response = requests.get(repo_languages_url, headers=headers)
        if response.status_code == 200:
            languages_data = response.json()
            if 'Jupyter Notebook' in languages_data:
                notebook_count += 1
                continue  # Skip Jupyter Notebook language
            repo_languages = []
            total_bytes = sum(languages_data.values())
            for language, bytes_count in languages_data.items():
                language_percentage = (bytes_count / total_bytes) * 100
                repo_languages.append({'language': language, 'percentage': f"{language_percentage:.2f}%"})
                languages_usage[language] = languages_usage.get(language, 0) + bytes_count
            repositories.append({'name': repo['name'], 'languages': repo_languages})

    # Calculate percentage for each language
    total_bytes = sum(languages_usage.values())
    languages_percentages = {language: f"{(bytes_count / total_bytes) * 100:.2f}%" for language, bytes_count in languages_usage.items()}
    notebook_percentage = f"{(notebook_count / total_repos) * 100:.2f}%"

    return {
        'user_details': required_user_details,
        'languages_percentages': languages_percentages,
        'notebook_percentage': notebook_percentage,
        'repositories': repositories
    }

# GitHub username to fetch details for
github_username = 'RAKESH-L'
# Your personal access token
access_token = 'YOUR-ACCESS-TOKEN'     #please enter your access token
details = fetch_github_details(github_username, access_token)
if details:
    print(json.dumps(details, indent=4))
