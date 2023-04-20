from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests
from socket import gaierror

app = Flask(__name__)
app.secret_key = "supersecretkey"

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/authenticate', methods=['GET', 'POST'])
def authenticate():
    # Check if access token is still valid
    access_token = session.get('access_token')
    backup_server = session.get('backup_server')
    if access_token and backup_server:
        if is_token_valid(backup_server, access_token):
            flash("You are already authenticated.")
            return redirect(url_for('welcome'))
        else:
            session.pop('access_token', None)
            session.pop('backup_server', None)
            flash("Session expired. Please authenticate again.")
            return redirect(url_for('authenticate'))

    if request.method == 'POST':
        backup_server = request.form['backup_server']
        username = request.form['username']
        password = request.form['password']

        try:
            access_token = get_access_token(backup_server, username, password)
        except requests.exceptions.RequestException as e:
            flash(f"Connection error: {str(e)}")
            return render_template('authenticate.html')
        else:
            if access_token:
                session['access_token'] = access_token
                session['backup_server'] = backup_server
                flash("Authentication successful.")
                return redirect(url_for('welcome'))
            else:
                flash("Authentication failed. Check your credentials and try again.")

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

@app.route('/list_repositories')
def list_repositories():
    access_token = session.get('access_token')
    backup_server = session.get('backup_server')

    if access_token and backup_server:
        repositories = get_repositories(backup_server, access_token)
        return render_template('list_repositories.html', repositories=repositories)
    else:
        flash("Please authenticate first.")
        return redirect(url_for('authenticate'))

@app.route('/list_jobs')
def list_jobs():
    access_token = session.get('access_token')
    backup_server = session.get('backup_server')

    if access_token and backup_server:
        jobs = get_jobs(backup_server, access_token)
        return render_template('list_jobs.html', jobs=jobs)
    else:
        flash("Please authenticate first.")
        return redirect(url_for('authenticate'))

@app.route('/job_action/<string:job_id>/<string:action>', methods=['POST'])
def job_action(job_id, action):
    access_token = session.get('access_token')
    backup_server = session.get('backup_server')

    if access_token and backup_server:
        success = execute_job_action(backup_server, access_token, job_id, action)

        if success:
            flash(f"Job {action} successfully.")
        else:
            flash(f"Failed to {action} the job.")
    else:
        flash("Please authenticate first.")

    return redirect(url_for('list_jobs'))

@app.route('/start_job/<job_id>', methods=['POST'])
def start_job(job_id):
    access_token = session.get('access_token')
    backup_server = session.get    ('backup_server')

    if access_token and backup_server:
        success = start_job(backup_server, access_token, job_id)

        if success:
            flash("Job started successfully.")
        else:
            flash("Failed to start the job.")
    else:
        flash("Please authenticate first.")

    return redirect(url_for('list_jobs'))

@app.route('/stop_job/<job_id>', methods=['POST'])
def stop_job(job_id):
    access_token = session.get('access_token')
    backup_server = session.get('backup_server')

    if access_token and backup_server:
        success = stop_job(backup_server, access_token, job_id)

        if success:
            flash("Job stopped successfully.")
        else:
            flash("Failed to stop the job.")
    else:
        flash("Please authenticate first.")

    return redirect(url_for('list_jobs'))

@app.route('/logout')
def logout():
    session.pop('access_token', None)
    session.pop('backup_server', None)
    flash("You have been logged out.")
    return redirect(url_for('welcome'))

@app.route('/list_object_restore_points')
def list_object_restore_points():
    access_token = session.get('access_token')
    backup_server = session.get('backup_server')

    if access_token and backup_server:
        object_restore_points = get_object_restore_points(backup_server, access_token)
        return render_template('list_object_restore_points.html', object_restore_points=object_restore_points)
    else:
        flash("Please authenticate first.")
        return redirect(url_for('authenticate'))

@app.route('/server_info')
def server_info():
    access_token = session.get('access_token')
    backup_server = session.get('backup_server')

    if access_token and backup_server:
        server_info = get_server_info(backup_server, access_token)
        print("Server Info:", server_info)
        return render_template('server_info.html', server_info=server_info)
    else:
        flash("Please authenticate first.")
        return redirect(url_for('authenticate'))

def get_repositories(backup_server, access_token):
    repositories_url = f"https://{backup_server}:9419/api/v1/backupInfrastructure/repositories"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "x-api-version": "1.1-rev0"
    }
    repositories_response = requests.get(repositories_url, headers=headers, verify=False)
    repositories_response.raise_for_status()

    json_response = repositories_response.json()
    print("JSON response:", json_response)

    return json_response["data"]

def get_access_token(backup_server, username, password):
    auth_url = f"https://{backup_server}:9419/api/oauth2/token"
    headers = {"x-api-version": "1.1-rev0"}
    data = {
        "grant_type": "password",
        "username": username,
        "password": password,
    }

    try:
        response = requests.post(auth_url, headers=headers, data=data, verify=False)
    except ConnectionError as e:
        print(f"Error connecting to server: {e}")
        return None

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

def get_jobs(backup_server, access_token):
    jobs_url = f"https://{backup_server}:9419/api/v1/jobs"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "x-api-version": "1.1-rev0"
    }
    jobs_response = requests.get(jobs_url, headers=headers, verify=False)
    jobs_response.raise_for_status()

    json_response = jobs_response.json()
    print("JSON response:", json_response)

    return json_response["data"]

def execute_job_action(backup_server, access_token, job_id, action):
    job_action_url = f"https://{backup_server}:9419/api/v1/jobs/{job_id}?action={action}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "x-api-version": "1.1-rev0"
    }
    job_action_response = requests.post(job_action_url, headers=headers, verify=False)

    if job_action_response.status_code == 204:
        return True
    else:
        return False
    
def is_token_valid(backup_server, access_token):
    test_url = f"https://{backup_server}:9419/api/v1/whoAmI"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "x-api-version": "1.1-rev0"
    }
    test_response = requests.get(test_url, headers=headers, verify=False)

    return test_response.status_code == 200

def get_object_restore_points(backup_server, access_token):
    object_restore_points_url = f"https://{backup_server}:9419/api/v1/objectRestorePoints"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "x-api-version": "1.1-rev0"
    }
    object_restore_points_response = requests.get(object_restore_points_url, headers=headers, verify=False)
    object_restore_points_response.raise_for_status()

    json_response = object_restore_points_response.json()
    print("JSON response:", json_response)

    return json_response["data"]

def get_server_info(backup_server, access_token):
    server_info_url = f'https://{backup_server}:9419/api/v1/serverInfo'
    headers = {
        "Authorization": f"Bearer {access_token}",
        "x-api-version": "1.1-rev0"
    }
    server_info_response = requests.get(server_info_url, headers=headers, verify=False)
    server_info_response.raise_for_status()

    json_response = server_info_response.json()
    print("JSON response:", json_response)

    return {
        "installation_id": json_response.get("vbrId", "N/A"),
        "name": json_response.get("name", "N/A"),
        "build_number": json_response.get("buildVersion", "N/A"),
        "cumulative_patches": json_response.get("patches", []),
    }

if __name__ == '__main__':
    app.run(debug=True)

