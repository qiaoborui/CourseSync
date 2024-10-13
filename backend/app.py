from flask import Flask, request, Response, redirect
from academic_calendar_service import AcademicCalendarService
import re

app = Flask(__name__)

def is_apple_device(user_agent):
    apple_devices = ['iphone', 'ipad', 'ipod', 'mac']
    return any(device in user_agent.lower() for device in apple_devices)

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
        
        user_agent = request.headers.get('User-Agent', '')
        
        if is_apple_device(user_agent):
            # For Apple devices, use webcal protocol
            webcal_url = request.url.replace('http', 'webcal', 1)
            return redirect(webcal_url, code=302)
        else:
            # For non-Apple devices, use https and add Content-Disposition header
            response = Response(calendar_data, mimetype='text/calendar')
            response.headers['Content-Disposition'] = 'attachment; filename=calendar.ics'
            return response
    except ValueError as e:
        return str(e), 400

if __name__ == '__main__':
    app.run(debug=True)
