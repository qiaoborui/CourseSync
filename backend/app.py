from flask import Flask, request, Response, redirect
from academic_calendar_service import AcademicCalendarService
from datetime import datetime

app = Flask(__name__)

@app.route('/class', methods=['GET'])
def get_academic_calendar():
    school = request.args.get('school', default='xauat')
    username = request.args.get('username')
    password = request.args.get('password') or request.args.get('passwd')
    filter_type = request.args.get('filter')
    
    if not username or not password:
        return "缺少用户名或密码", 400
    
    try:
        service = AcademicCalendarService(school, username, password)
        
        event_filter = None
        if filter_type == 'future':
            current_time = datetime.now()
            event_filter = lambda event: event['start'] > current_time
        elif filter_type == 'no_classroom':
            event_filter = lambda event: event['roomZh'] != '未知地点'
        
        calendar_data = service.generate_calendar(event_filter)
        
        if calendar_data is None:
            return "认证失败", 401
        
        response = Response(calendar_data, mimetype='text/calendar')
        response.headers['Content-Disposition'] = 'attachment; filename=calendar.ics'
        return response
    except ValueError as e:
        return str(e), 400

if __name__ == '__main__':
    app.run(debug=True)
