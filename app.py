from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3
import os
import pandas as pd
import io
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
                filename TEXT,
                members TEXT,
                advisor TEXT,
                committee1 TEXT,
                committee2 TEXT,
                semester TEXT,
                theory TEXT,
                advisor_meeting_dates TEXT
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
        language_list = request.form.getlist('programming_language[]')
        language = ",".join([lang.strip() for lang in language_list if lang.strip()])

        framework_list = request.form.getlist('framework[]')
        framework = ",".join([fw.strip() for fw in framework_list if fw.strip()])

        libraries = request.form['libraries']
        members = request.form['members']
        advisor = request.form['advisor']
        committee1 = request.form['committee1']
        committee2 = request.form['committee2']
        semester = request.form['semester']
        theory = request.form['theory']
        advisor_meeting_dates_list = request.form.getlist('advisor_meeting_dates[]')
        advisor_meeting_dates = ",".join([date for date in advisor_meeting_dates_list if date.strip()])

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
                SET name = ?, description = ?, language = ?, framework = ?, libraries = ?,
                    filename = ?, members = ?, advisor = ?, committee1 = ?, committee2 = ?,
                    semester = ?, theory = ?
                WHERE id = ?
            """, (name, description, language, framework, libraries, filename_str,
                  members, advisor, committee1, committee2, semester, theory, project_id))
        else:
            cursor.execute("""
                UPDATE projects
                SET name = ?, description = ?, language = ?, framework = ?, libraries = ?,
                    members = ?, advisor = ?, committee1 = ?, committee2 = ?,
                    semester = ?, theory = ?
                WHERE id = ?
            """, (name, description, language, framework, libraries,
                  members, advisor, committee1, committee2, semester, theory, project_id))
        
        if saved_filenames:
            cursor.execute("""
                UPDATE projects
                SET name = ?, description = ?, language = ?, framework = ?, libraries = ?,
                    filename = ?, members = ?, advisor = ?, committee1 = ?, committee2 = ?,
                    semester = ?, theory = ?, advisor_meeting_dates = ?
                WHERE id = ?
            """, (name, description, language, framework, libraries, filename_str,
                  members, advisor, committee1, committee2, semester, theory,
                  advisor_meeting_dates, project_id))
        else:
            cursor.execute("""
                UPDATE projects
                SET name = ?, description = ?, language = ?, framework = ?, libraries = ?,
                    members = ?, advisor = ?, committee1 = ?, committee2 = ?,
                    semester = ?, theory = ?, advisor_meeting_dates = ?
                WHERE id = ?
            """, (name, description, language, framework, libraries,
                  members, advisor, committee1, committee2, semester, theory,
                  advisor_meeting_dates, project_id))

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
    
    language_list = request.form.getlist('programming_language[]')
    language = ",".join([lang.strip() for lang in language_list if lang.strip()])

    framework_list = request.form.getlist('framework[]')
    framework = ",".join([fw.strip() for fw in framework_list if fw.strip()])

    libraries = request.form['libraries']
    members = request.form['members']
    advisor = request.form['advisor']
    committee1 = request.form['committee1']
    committee2 = request.form['committee2']
    semester = request.form['semester']
    theory = request.form['theory']
    advisor_meeting_dates_list = request.form.getlist('advisor_meeting_dates[]')
    advisor_meeting_dates = ",".join([date for date in advisor_meeting_dates_list if date.strip()])

    files = request.files.getlist('files')
    saved_filenames = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            saved_filenames.append(filename)

    filename_str = ",".join(saved_filenames) if saved_filenames else None

    conn = sqlite3.connect('projects.db')
    conn.execute("""
        INSERT INTO projects (name, description, language, framework, libraries, filename,
                              members, advisor, committee1, committee2, semester, theory,
                              advisor_meeting_dates)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, description, language, framework, libraries, filename_str,
          members, advisor, committee1, committee2, semester, theory,
          advisor_meeting_dates))
    conn.commit()
    conn.close()
    flash('เพิ่มโครงงานใหม่สำเร็จ')
    return redirect('/')

@app.route('/export_projects', methods=['GET'])
def export_projects():
    conn = sqlite3.connect('projects.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    conn.close()

    df = pd.DataFrame(rows, columns=columns)

    # แปลง DataFrame เป็นไฟล์ Excel ในหน่วยความจำ
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Projects')

    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='projects.xlsx'
    )

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
