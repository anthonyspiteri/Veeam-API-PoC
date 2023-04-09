from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests

app = Flask(__name__)
app.secret_key = "supersecretkey"

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/authenticate', methods=['GET', 'POST'])
def authenticate():
    if request.method == 'POST':
        backup_server = request.form['backup_server']
        username = request.form['username']
        password = request.form['password']

        access_token = get_access_token(backup_server, username, password)

        if access_token:
            session['access_token'] = access_token
            session['backup_server'] = backup_server
            flash("Authentication successful. Choose an option from the sidebar.")
            return redirect(url_for('welcome'))
        else:
            return render_template('authentication_failed.html')
    authenticated = 'access_token' in session
    return render_template('authenticate.html', authenticated=authenticated)

@app.route('/list_vcenters')
def list_vcenters():
    access_token = session.get('access_token')
    backup_server = session.get('backup_server')

    if access_token and backup_server:
        vcenters = get_vcenters(backup_server, access_token)
        print("vCenters:", vcenters)
        return render_template('list_vcenters.html', vcenters=vcenters)
    else:
        flash("Please authenticate first.")
        return redirect(url_for('authenticate'))

def get_access_token(backup_server, username, password):
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
