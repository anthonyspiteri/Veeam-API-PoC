from flask import Flask, render_template_string, request, redirect, url_for
import requests

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        backup_server = request.form['backup_server']
        username = request.form['username']
        password = request.form['password']
        
        access_token = authenticate(backup_server, username, password)
        
        if access_token:
            vcenters = get_vcenters(backup_server, access_token)
            return render_template_string('''
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Available vCenters</title>
                </head>
                <body>
                    <h1>Available vCenters</h1>
                    <ul>
                        {% for vcenter in vcenters %}
                            <li>{{ vcenter.inventoryObject.name }}</li>
                        {% endfor %}
                    </ul>
                </body>
            </html>
            ''', vcenters=vcenters)
        else:
            return render_template_string('''
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Authentication Failed</title>
                </head>
                <body>
                    <h1>Authentication Failed</h1>
                    <p>Check your credentials and try again.</p>
                    <a href="{{ url_for('index') }}">Go back to the form</a>
                </body>
            </html>
            ''')

    return render_template_string('''
    <!DOCTYPE html>
    <html>
        <head>
            <title>Veeam Authentication</title>
        </head>
        <body>
            <h1>Veeam Authentication</h1>
            <form method="post">
                <label for="backup_server">Backup Server:</label>
                <input type="text" id="backup_server" name="backup_server" required>
                <br>
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" required>
                <br>
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required>
                <br>
                <input type="submit" value="Authenticate">
            </form>
        </body>
    </html>
    ''')

def authenticate(backup_server, username, password):
    auth_url = f"https://{backup_server}:9419/api/oauth2/token"
    headers = {"x-api-version": "1.1-rev0"}
    data = {
        "grant_type": "password",
        "username": username,
        "password": password,
    }

    response = requests.post(auth_url, headers=headers, data=data, verify=False)
    
    if response.status_code == 200:
        access_token = response.json()["access_token"]
        return access_token
    else:
        return None

def get_vcenters(backup_server, access_token):
    vcenters_url = f"https://{backup_server}:9419/api/v1/inventory/vmware/hosts"
    headers = {
                "Authorization": f"Bearer {access_token}",
                "x-api-version": "1.1-rev0"
    }
    vcenters_response = requests.get(vcenters_url, headers=headers, verify=False)
    vcenters_response.raise_for_status()

    json_response = vcenters_response.json()
    print("JSON response:", json_response)

    return json_response["data"]

if __name__ == '__main__':
    app.run(debug=True)