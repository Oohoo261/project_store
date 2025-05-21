from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    with sqlite3.connect('projects.db') as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                language TEXT,
                framework TEXT,
                libraries TEXT,
                filename TEXT
            )
        ''')

@app.route('/')
def index():
    conn = sqlite3.connect('projects.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, language, framework FROM projects")
    projects = cursor.fetchall()
    conn.close()
    return render_template('index.html', projects=projects)

@app.route('/project/<int:project_id>')
def view_project(project_id):
    conn = sqlite3.connect('projects.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    project = cursor.fetchone()
    conn.close()
    return render_template('project_detail.html', project=project)

@app.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    conn = sqlite3.connect('projects.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['project_name']
        description = request.form['description']
        language = request.form['programming_language']
        framework = request.form['framework']
        libraries = request.form['libraries']

        files = request.files.getlist('files')
        saved_filenames = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                saved_filenames.append(filename)
        if saved_filenames:
            filename_str = ",".join(saved_filenames)
            cursor.execute("""
                UPDATE projects
                SET name = ?, description = ?, language = ?, framework = ?, libraries = ?, filename = ?
                WHERE id = ?
            """, (name, description, language, framework, libraries, filename_str, project_id))
        else:
            cursor.execute("""
                UPDATE projects
                SET name = ?, description = ?, language = ?, framework = ?, libraries = ?
                WHERE id = ?
            """, (name, description, language, framework, libraries, project_id))
        conn.commit()
        conn.close()
        flash('แก้ไขโครงงานสำเร็จ')
        return redirect(url_for('view_project', project_id=project_id))

    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    project = cursor.fetchone()
    conn.close()
    return render_template('edit_project.html', project=project)

@app.route('/delete_project/<int:project_id>')
def delete_project(project_id):
    conn = sqlite3.connect('projects.db')
    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    if row and row[0]:
        filenames = row[0].split(',')
        for filename in filenames:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename.strip())
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                print(f"ลบไฟล์ไม่สำเร็จ: {e}")

    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()
    flash('ลบโครงงานสำเร็จ')
    return redirect('/')


@app.route('/submit_project', methods=['POST'])
def submit_project():
    name = request.form['project_name']
    description = request.form['description']
    language = request.form['programming_language']
    framework = request.form['framework']
    libraries = request.form['libraries']

    files = request.files.getlist('files')
    saved_filenames = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            saved_filenames.append(filename)

    filename_str = ",".join(saved_filenames) if saved_filenames else None

    conn = sqlite3.connect('projects.db')
    conn.execute("INSERT INTO projects (name, description, language, framework, libraries, filename) VALUES (?, ?, ?, ?, ?, ?)",
             (name, description, language, framework, libraries, filename_str))
    conn.commit()
    conn.close()
    flash('เพิ่มโครงงานใหม่สำเร็จ')
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
