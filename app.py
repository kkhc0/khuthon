from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.utils import secure_filename
from urllib.parse import unquote
from collections import defaultdict
import csv
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = os.path.join('../static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DATA_FOLDER = '../data'
os.makedirs(DATA_FOLDER, exist_ok=True)
REVIEW_CSV = os.path.join(DATA_FOLDER, 'reviewer_data.csv')

# ===== 초기 진입 화면 (로그인 화면) =====
@app.route('/', methods=['GET'])
def home():
    return render_template('login.html')

# ===== 역할 선택 후 로그인 처리 =====
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    role = request.form['role']  # 'young' 또는 'senior'

    session['username'] = username
    session['role'] = role

    if role == 'young':
        return redirect(url_for('youth_dashboard'))  # 청년용 대시보드
    elif role == 'senior':
        return redirect(url_for('farmer_dashboard'))  # 농민용 대시보드

# ===== 농민 대시보드 =====
@app.route('/farmer')
def farmer_dashboard():
    return render_template('farmer_dashboard.html')

#==== 청년 대시보드 ====
@app.route('/youth')
def youth_dashboard():
    return render_template('youth_dashboard.html')

#==== 농민 할 일 주기 =====
@app.route('/task_register')
def task_register():
    return render_template('task_register.html')

#==== 전국지도 ====
@app.route('/map')
def map_page():
    return render_template('youth_map.html')

#==== 충북 ====
@app.route('/chungbuk')
def chungbuk():
    return render_template('chungbuk.html')

#==== 충남 ====
@app.route('/chungnam')
def chungnam():
    return render_template('chungnam.html')

#==== 경북 ====
@app.route('/gyeongbuk')
def gyeongbuk():
    return render_template('gyeongbuk.html')

#==== 경남 ====
@app.route('/gyeongnam')
def gyeongnam():
    return render_template('gyeongnam.html')

#==== 강원 ====
@app.route('/gangwon')
def gangwon():
    return render_template('gangwon.html')

#==== 전북 ====
@app.route('/jeonbuk')
def jeonbuk():
    return render_template('jeonbuk.html')

#==== 전남 ====
@app.route('/jeonnam')
def jeonnam():
    return render_template('jeonnam.html')

#==== 경기 ====
@app.route('/gyeonggi')
def gyeonggi():
    return render_template('gyeonggi.html')

#==== 제주 ====
@app.route('/jeju')
def jeju():
    return render_template('jeju.html')

#==== farmer_data.csv 저장 기능 ====
@app.route('/submit_task', methods=['POST'])
def submit_task():
    desc = request.form['desc']
    crop = request.form['crop']
    date = request.form['date']
    location = request.form['location']
    tasks = request.form.getlist('tasks')

    filepath = '../data/farmer_data.csv'
    is_new = not os.path.exists(filepath)

    with open(filepath, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(['주소', '날짜', '농축산물', '작업들', '상세 설명'])
        writer.writerow([location, date, crop, ', '.join(tasks), desc])

    return redirect('/farmer')

#==== 사진 리뷰 ====
@app.route('/picture')
def picture_review():
    return render_template('picture_review.html')

#==== 사진 리뷰 저장 기능 ====
@app.route('/submit_review', methods=['POST'])
def submit_review():
    # 1. 폼에서 값 가져오기
    date = request.form['date']
    location = request.form['location']
    crop_type = request.form['type']
    activities = request.form['activities']

    # 2. 사진 저장
    photo = request.files['photo']
    if photo and photo.filename != '':
        filename = secure_filename(photo.filename)
        photo_path = os.path.join(UPLOAD_FOLDER, filename)
        photo.save(photo_path)
        photo_url = f'../static/uploads/{filename}'  # CSV에 경로로 저장
    else:
        photo_url = ''

    # 3. reviewer_data.csv에 저장
    is_new = not os.path.exists(REVIEW_CSV)
    with open(REVIEW_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(['날짜', '장소', '작물', '활동들', '사진경로'])
        writer.writerow([date, location, crop_type, activities, photo_url])

    # 4. 완료 후 청년 대시보드로 이동
    return redirect('/youth')

#==== detail ====
@app.route('/detail/<addr>')
def detail_page(addr):
    farms = load_farm_data_()
    reviews = load_review_data_()
    decoded_addr = unquote(addr)

    if decoded_addr not in farms:
        return "해당 주소의 데이터가 없습니다.", 404

    # ✅ 작업 항목 하나하나에 모든 정보 담기
    combined_tasks = []
    for 날짜, 작물, 작업들, 설명 in farms[decoded_addr]:
        for 작업 in 작업들.split(', '):
            combined_tasks.append({
                'date': 날짜,
                'crop': 작물,
                'task': 작업,
                'desc': 설명
            })


    # ✅ 여기부터 새로 넣기
    matched_images = []
    for loc, paths in reviews.items():
        if decoded_addr in loc or loc in decoded_addr:
            if isinstance(paths, list):
                matched_images.extend(paths)
            else:
                matched_images.append(paths)

    image_list = [path.replace('../static/', '') for path in matched_images[-3:]]

    return render_template(
    'detail_page.html',
    addr=decoded_addr,
    tasks=combined_tasks,
    images=image_list
    )



# ===== farmer_data.csv -> 주소: (날짜, 작물, 작업, 설명) =====
def load_farm_data():
    filepath = '../data/farmer_data.csv'
    data = {}
    if os.path.exists(filepath):
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                addr = row['주소']
                value = (row['날짜'], row['농축산물'], row['작업들'], row['상세 설명'])
                data[addr] = value
    return data

def load_farm_data_():
    filepath = '../data/farmer_data.csv'
    data = defaultdict(list)
    if os.path.exists(filepath):
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                addr = row['주소']
                value = (row['날짜'], row['농축산물'], row['작업들'], row['상세 설명'])
                data[addr].append(value)  # 리스트에 계속 추가
    return data

# ===== reviewer_data.csv -> 주소: 사진경로 =====
def load_review_data():
    filepath = '../data/reviewer_data.csv'
    data = {}
    if os.path.exists(filepath):
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                addr = row['장소']
                data[addr] = row['사진경로']
    return data

def load_review_data_():
    filepath = '../data/reviewer_data.csv'
    data = defaultdict(list)
    if os.path.exists(filepath):
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                addr = row['장소']
                data[addr].append(row['사진경로'])  # 여러 개 저장
    return data
#==== 정읍시 ====
@app.route('/jeonbuk_jeongeup')
def jeongeup_page():
    farms = load_farm_data()
    reviews = load_review_data()

    # 정읍시 필터링
    jeongeup_farms = {k: v for k, v in farms.items() if '전라북도 정읍시' in k}
    jeongeup_reviews = {k: v for k, v in reviews.items() if '전라북도 정읍시' in k}
    return render_template('jeonbuk_jeongeup.html', farms=jeongeup_farms, images=jeongeup_reviews)




# ===== 앱 실행 =====
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

