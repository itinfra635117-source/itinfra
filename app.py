# Admin reset user password


# ...existing code...



# Edit and Delete for Requests
# Move all new route definitions below app initialization
def register_edit_delete_routes(app):
    @app.route('/admin_edit/<int:req_id>', methods=['GET', 'POST'])
    def admin_edit_request(req_id):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        # Find request in all tables
        all_tables = [
            'system_service_requests',
            'printer_service_requests',
            'network_service_requests',
            'projector_service_requests',
            'other_service_requests'
        ]
        req = None
        table_found = None
        for table in all_tables:
            url = f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{req_id}"
            resp = requests.get(url, headers=SUPABASE_HEADERS)
            if resp.status_code == 200 and resp.json():
                req = resp.json()[0]
                table_found = table
                break
        if not req:
            return "Request not found", 404
        if request.method == 'POST':
            # Update fields (example: name, institution, etc.)
            update_data = {
                "name": request.form.get('name', req['name']),
                "institution": request.form.get('institution', req['institution']),
                # Add more fields as needed
            }
            patch_url = f"{SUPABASE_URL}/rest/v1/{table_found}?id=eq.{req_id}"
            requests.patch(patch_url, headers=SUPABASE_HEADERS, json=update_data)
            return redirect(url_for('admin_dashboard'))
        return render_template('admin_edit_request.html', req=req)

    @app.route('/admin_delete/<int:req_id>', methods=['GET'])
    def admin_delete_request(req_id):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        all_tables = [
            'system_service_requests',
            'printer_service_requests',
            'network_service_requests',
            'projector_service_requests',
            'other_service_requests'
        ]
        for table in all_tables:
            url = f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{req_id}"
            requests.delete(url, headers=SUPABASE_HEADERS)
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin_user_edit/<int:user_id>', methods=['GET', 'POST'])
    def admin_user_edit(user_id):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        url = f"{SUPABASE_URL}/rest/v1/users?id=eq.{user_id}"
        resp = requests.get(url, headers=SUPABASE_HEADERS)
        if resp.status_code != 200 or not resp.json():
            return "User not found", 404
        user = resp.json()[0]
        if request.method == 'POST':
            update_data = {
                "name": request.form.get('name', user['name']),
                "institution": request.form.get('institution', user['institution']),
                "mobile": request.form.get('mobile', user['mobile']),
                "email": request.form.get('email', user['email'])
            }
            patch_url = f"{SUPABASE_URL}/rest/v1/users?id=eq.{user_id}"
            requests.patch(patch_url, headers=SUPABASE_HEADERS, json=update_data)
            return redirect(url_for('admin_dashboard'))
        return render_template('admin_edit_user.html', user=user)

    @app.route('/admin_user_delete/<int:user_id>', methods=['GET'])
    def admin_user_delete(user_id):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        url = f"{SUPABASE_URL}/rest/v1/users?id=eq.{user_id}"
        requests.delete(url, headers=SUPABASE_HEADERS)
        return redirect(url_for('admin_dashboard'))


import requests
import hashlib
from flask import Flask, render_template, request, redirect, session, url_for, make_response, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
register_edit_delete_routes(app)

# Route to serve images from img folder
@app.route('/img/<filename>')
def img(filename):
    return send_from_directory('img', filename)

# Route to serve static CSS files
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/admin_status/<int:req_id>', methods=['GET', 'POST'])
def admin_update_status(req_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    # Find request in all tables
    all_tables = [
        'system_service_requests',
        'printer_service_requests',
        'network_service_requests',
        'projector_service_requests',
        'other_service_requests'
    ]
    req = None
    table_found = None
    for table in all_tables:
        url = f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{req_id}"
        resp = requests.get(url, headers=SUPABASE_HEADERS)
        if resp.status_code == 200 and resp.json():
            req = resp.json()[0]
            table_found = table
            break
    if not req:
        return "Request not found", 404
    if request.method == 'POST':
        new_status = request.form['status'].strip().lower()
        notes = request.form.get('notes', '')
        # Update status in request table
        patch_url = f"{SUPABASE_URL}/rest/v1/{table_found}?id=eq.{req_id}"
        patch_data = {"status": new_status}
        patch_resp = requests.patch(patch_url, headers=SUPABASE_HEADERS, json=patch_data)
        # Log status update in request_status_updates table
        log_data = {
            "request_id": req_id,
            "request_type": req.get('type', table_found.replace('_service_requests', '').replace('_', ' ').title()),
            "institution": req.get('institution'),
            "name": req.get('name'),
            "status": new_status,
            "updated_by": session.get('admin_name', 'admin'),
            "notes": notes
        }
        log_url = f"{SUPABASE_URL}/rest/v1/request_status_updates"
        requests.post(log_url, headers=SUPABASE_HEADERS, json=[log_data])
        return redirect(url_for('admin_dashboard'))
    # Pass request info to form
    req['type'] = req.get('type', table_found.replace('_service_requests', '').replace('_', ' ').title())
    if 'status' not in req or not req['status']:
        req['status'] = 'pending'
    print('DEBUG admin_update_status req:', req)
    return render_template('admin_update_status.html', req=req)

def get_admin_by_email(email):
    url = f"{SUPABASE_URL}/rest/v1/admin?email=eq.{email.strip()}"
    resp = requests.get(url, headers=SUPABASE_HEADERS)
    print("Admin Supabase response:", resp.status_code, resp.text)
    if resp.status_code == 200 and resp.json():
        return resp.json()[0]
    return None

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        admin = get_admin_by_email(email)
        if admin and admin['password'].strip() == password:
            session['admin_id'] = admin['id']
            session['admin_name'] = admin['name']
            return redirect(url_for('admin_dashboard'))
        else:
            error = 'Invalid admin email or password. Please try again.'
        return render_template('admin_login.html', error=error)
    return render_template('admin_login.html', error=error)

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    # Fetch all requests from all tables
    all_tables = [
        'system_service_requests',
        'printer_service_requests',
        'network_service_requests',
        'projector_service_requests',
        'other_service_requests'
    ]
    requests_list = []
    # Fetch all status updates once for efficiency
    status_url = f"{SUPABASE_URL}/rest/v1/request_status_updates?order=updated_at.desc"
    status_resp = requests.get(status_url, headers=SUPABASE_HEADERS)
    status_updates = status_resp.json() if status_resp.status_code == 200 else []

    for table in all_tables:
        url = f"{SUPABASE_URL}/rest/v1/{table}"
        resp = requests.get(url, headers=SUPABASE_HEADERS)
        if resp.status_code == 200:
            for req in resp.json():
                req['type'] = table.replace('_service_requests', '').replace('_', ' ').title()
                # Find latest status update for this request
                latest_status = next((s for s in status_updates if s['request_id'] == req['id']), None)
                if latest_status:
                    req['status'] = latest_status['status']
                    req['date'] = str(latest_status.get('updated_at', ''))[:10] if latest_status.get('updated_at') else ''
                else:
                    req['status'] = req.get('status', 'pending')
                    req['date'] = str(req.get('created_at', ''))[:10] if req.get('created_at') else req.get('date', '')
                requests_list.append(req)
    # Filter/search logic (basic)
    institution = request.args.get('institution', '')
    type_filter = request.args.get('type', '')
    status = request.args.get('status', '')
    date = request.args.get('date', '')
    filtered_requests = []
    for req in requests_list:
        if institution and req.get('institution') != institution:
            continue
        if type_filter and req.get('type') != type_filter:
            continue
        if status and req.get('status', '') != status:
            continue
        if date and str(req.get('created_at', '')).split('T')[0] != date:
            continue
        filtered_requests.append(req)
    # Stats
    stats = {
        'total': len(requests_list),
        'resolved': sum(1 for r in requests_list if r.get('status') == 'resolved'),
        'pending': sum(1 for r in requests_list if r.get('status') == 'pending'),
        'in_progress': sum(1 for r in requests_list if r.get('status') == 'in_progress'),
    }
    return render_template('admin_dashboard.html', stats=stats, requests=filtered_requests)

@app.route('/export_requests')
def export_requests():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    try:
        # Get status filter from query params
        status_filter = request.args.get('status', '').strip().lower()

        # Fetch all requests from all tables (same logic as admin_dashboard)
        all_tables = [
            'system_service_requests',
            'printer_service_requests',
            'network_service_requests',
            'projector_service_requests',
            'other_service_requests'
        ]
        requests_list = []

        # Fetch all status updates once for efficiency
        status_url = f"{SUPABASE_URL}/rest/v1/request_status_updates?order=updated_at.desc"
        status_resp = requests.get(status_url, headers=SUPABASE_HEADERS)
        status_updates = status_resp.json() if status_resp.status_code == 200 else []

        for table in all_tables:
            url = f"{SUPABASE_URL}/rest/v1/{table}"
            resp = requests.get(url, headers=SUPABASE_HEADERS)
            if resp.status_code == 200:
                for req in resp.json():
                    req['type'] = table.replace('_service_requests', '').replace('_', ' ').title()
                    # Find latest status update for this request
                    latest_status = next((s for s in status_updates if s['request_id'] == req['id']), None)
                    if latest_status:
                        req['status'] = latest_status['status']
                        req['date'] = str(latest_status.get('updated_at', ''))[:10] if latest_status.get('updated_at') else ''
                    else:
                        req['status'] = req.get('status', 'pending')
                        req['date'] = str(req.get('created_at', ''))[:10] if req.get('created_at') else req.get('date', '')
                    # Apply status filter if set
                    if status_filter and req['status'] != status_filter:
                        continue
                    requests_list.append(req)

        # Create CSV content
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Write comprehensive header with all possible fields
        headers = [
            'ID', 'Created At', 'Institution', 'Type', 'Name', 'Department',
            'Email', 'Mobile', 'Status', 'Date', 'Image URL',
            'System Issues', 'Printer Model', 'Printer Service',
            'Network Service', 'Projector Issues', 'Other Service'
        ]
        writer.writerow(headers)

        # Write data
        for req in requests_list:
            # Handle arrays properly
            system_issues = ', '.join(req.get('system_issues', [])) if req.get('system_issues') else ''
            printer_model = ', '.join(req.get('printer_model', [])) if req.get('printer_model') else ''
            projector_issues = ', '.join(req.get('projector_issues', [])) if req.get('projector_issues') else ''

            row = [
                req.get('id', ''),
                str(req.get('created_at', ''))[:19] if req.get('created_at') else '',
                req.get('institution', ''),
                req.get('type', ''),
                req.get('name', ''),
                req.get('department', ''),
                req.get('email', ''),
                req.get('mobile', ''),
                req.get('status', ''),
                req.get('date', ''),
                req.get('image_url', ''),
                system_issues,
                printer_model,
                req.get('printer_service', ''),
                req.get('network_service', ''),
                projector_issues,
                req.get('other_service', '')
            ]
            writer.writerow(row)

        # Create response
        csv_content = output.getvalue()
        output.close()

        response = make_response(csv_content)
        response.headers['Content-Disposition'] = 'attachment; filename=service_requests_export.csv'
        response.headers['Content-Type'] = 'text/csv'

        return response

    except Exception as e:
        print(f"Export error: {str(e)}")
        return f"Export failed: {str(e)}", 500

SUPABASE_URL = "https://atsewgcegvauctfygkcm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF0c2V3Z2NlZ3ZhdWN0Znlna2NtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg3MjIzNDcsImV4cCI6MjA3NDI5ODM0N30.GG4QpO32JwHuOUMxtFv-QdM9Sb_J-bvQH9QbPZm8c_s"
SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

app.secret_key = 'your_secret_key_here'

def get_user_by_email(email):
    url = f"{SUPABASE_URL}/rest/v1/users?email=eq.{email.strip()}"
    resp = requests.get(url, headers=SUPABASE_HEADERS)
    print("Supabase response:", resp.status_code, resp.text)
    if resp.status_code == 200 and resp.json():
        return resp.json()[0]
    return None
def insert_to_supabase(table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    response = requests.post(url, headers=SUPABASE_HEADERS, json=[data])
    return response.status_code == 201
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        name = request.form['name']
        institution = request.form['institution']
        mobile = request.form['mobile']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            error = 'Passwords do not match'
        elif get_user_by_email(email):
            error = 'Email already registered'
        else:
            data = {
                "name": name,
                "institution": institution,
                "mobile": mobile,
                "email": email,
                "password": password
            }
            url = f"{SUPABASE_URL}/rest/v1/users"
            resp = requests.post(url, headers=SUPABASE_HEADERS, json=[data])
            if resp.status_code == 201:
                return redirect(url_for('login'))
            else:
                error = 'Registration failed. Please try again.'
        return render_template('register.html', error=error)
    return render_template('register.html', error=error)
    response = requests.post(url, headers=SUPABASE_HEADERS, json=[data])
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        user = get_user_by_email(email)
        if user and user['password'].strip() == password:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            return redirect(url_for('index'))
        else:
            error = 'Invalid email or password. Please try again.'
        return render_template('login.html', error=error)
    return render_template('login.html', error=error)
    return response.status_code == 201



@app.route('/', methods=['GET'])
def home():
    return redirect(url_for('index'))

@app.route('/form', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        form = request.form
        institution = form.get('institution')
        name = form.get('name')
        department = form.get('department')
        email = form.get('email')
        mobile = form.get('mobile')
        service_type = form.get('service_type')

        # Handle image upload
        image_url = None
        if 'issue_image' in request.files:
            file = request.files['issue_image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                # Upload to Supabase Storage
                storage_url = f"{SUPABASE_URL}/storage/v1/object/Issue Images/{filename}"
                upload_headers = {
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": file.mimetype
                }
                upload_resp = requests.post(storage_url, headers=upload_headers, data=file.read())
                if upload_resp.status_code in [200, 201]:
                    image_url = f"{SUPABASE_URL}/storage/v1/object/public/Issue Images/{filename}"

        # Common data
        base_data = {
            "institution": institution,
            "name": name,
            "department": department,
            "email": email,
            "mobile": mobile,
            "image_url": image_url
        }

        # Route to correct table
        if service_type == "System Services":
            system_issues = request.form.getlist('system_issues')
            data = base_data.copy()
            data["system_issues"] = system_issues
            table = "system_service_requests"
        elif service_type == "Printer Services":
            printer_model = request.form.getlist('printer_model')
            printer_service = form.get('printer_service')
            data = base_data.copy()
            data["printer_model"] = printer_model
            data["printer_service"] = printer_service
            table = "printer_service_requests"
        elif service_type == "Network Services":
            network_service = form.get('network_service')
            data = base_data.copy()
            data["network_service"] = network_service
            table = "network_service_requests"
        elif service_type == "Projector":
            projector_issues = request.form.getlist('projector_issues')
            data = base_data.copy()
            data["projector_issues"] = projector_issues
            table = "projector_service_requests"
        elif service_type == "Other":
            other_service = form.get('other_service')
            data = base_data.copy()
            data["other_service"] = other_service
            table = "other_service_requests"
        else:
            # fallback: just store institution info
            data = base_data.copy()
            table = "institution_requests"

        success = insert_to_supabase(table, data)
        if success:
            return render_template('success.html')
        else:
            return "Error submitting request. Please try again.", 500
    return render_template('form.html')


# Logout route for both admin and user
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))



# View details of a service request (admin)
@app.route('/admin_view/<int:req_id>', methods=['GET'])
def admin_view_request(req_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    all_tables = [
        'system_service_requests',
        'printer_service_requests',
        'network_service_requests',
        'projector_service_requests',
        'other_service_requests'
    ]
    req = None
    table_found = None
    for table in all_tables:
        url = f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{req_id}"
        resp = requests.get(url, headers=SUPABASE_HEADERS)
        if resp.status_code == 200 and resp.json():
            req = resp.json()[0]
            table_found = table
            break
    if not req:
        return "Request not found", 404
    # Add type for display
    req['type'] = table_found.replace('_service_requests', '').replace('_', ' ').title()
    # Fetch latest status update for this request
    status_url = f"{SUPABASE_URL}/rest/v1/request_status_updates?request_id=eq.{req_id}&order=updated_at.desc"
    status_resp = requests.get(status_url, headers=SUPABASE_HEADERS)
    if status_resp.status_code == 200 and status_resp.json():
        latest_status = status_resp.json()[0]
        req['status'] = latest_status.get('status', req.get('status', 'pending'))
        req['date'] = str(latest_status.get('updated_at', ''))[:10] if latest_status.get('updated_at') else req.get('date', '')
    else:
        req['status'] = req.get('status', 'pending')
        req['date'] = str(req.get('created_at', ''))[:10] if req.get('created_at') else req.get('date', '')
    return render_template('admin_view_request.html', req=req)

# Admin reset user password
@app.route('/admin_user_reset/<int:user_id>', methods=['GET', 'POST'])
def admin_user_reset(user_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    url = f"{SUPABASE_URL}/rest/v1/users?id=eq.{user_id}"
    resp = requests.get(url, headers=SUPABASE_HEADERS)
    if resp.status_code != 200 or not resp.json():
        return "User not found", 404
    user = resp.json()[0]
    error = None
    if request.method == 'POST':
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        if not new_password:
            error = 'Password cannot be empty.'
        elif new_password != confirm_password:
            error = 'Passwords do not match.'
        else:
            patch_url = f"{SUPABASE_URL}/rest/v1/users?id=eq.{user_id}"
            patch_data = {"password": new_password}
            patch_resp = requests.patch(patch_url, headers=SUPABASE_HEADERS, json=patch_data)
            if patch_resp.status_code in [200, 204]:
                return redirect(url_for('admin_dashboard'))
            else:
                print('Supabase PATCH error:', patch_resp.status_code, patch_resp.text)
                error = 'Failed to reset password.'
    return render_template('admin_reset_user.html', user=user, error=error)

if __name__ == '__main__':
    app.run(debug=False)
