from flask import Flask, request, Response
from academic_calendar_service import AcademicCalendarService

app = Flask(__name__)

@app.route('/class', methods=['GET'])
def get_academic_calendar():
    school = request.args.get('school', default='xauat')
    username = request.args.get('username')
    password = request.args.get('password') or request.args.get('passwd')
    if not username or not password:
        return "缺少用户名或密码", 400
    
    try:
        service = AcademicCalendarService(school, username, password)
        calendar_data = service.generate_calendar()
        
        if calendar_data is None:
            return "认证失败", 401
        
        return Response(calendar_data, mimetype='text/calendar')
    except ValueError as e:
        return str(e), 400