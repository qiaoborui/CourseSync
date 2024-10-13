# Course Calendar Subscription

English | [中文](README_CN.md)

## Project Overview

This is a calendar subscription application designed for university students. The application allows students to easily synchronize their school's course schedules, exam arrangements, and other important events to their personal calendars.

Currently supported schools:
- Xi'an University of Architecture and Technology (XAUAT)
- Northwest A&F University (NWAFU)

## Main Features

- Automatic synchronization of XAUAT and NWAFU student course schedules
- Import exam schedules and important school dates
- Support for various calendar applications (such as Google Calendar, Apple Calendar, Outlook, etc.)
- Real-time updates to ensure information is always up-to-date

## How to Use

1. Visit our web application: [calendar-subscription-app.html](https://schedule.borry.org/l)
2. Select your school
3. Log in with your student account
4. Click the "Subscribe" button
5. Add the generated link to your preferred calendar application

## Contribution Guidelines

We welcome and appreciate any form of contribution! Here are some ways to participate in the project:

### Reporting Issues

If you find a bug or have a suggestion for a new feature, please create an issue on GitHub. Be sure to provide the following information:

- Detailed description of the issue
- Steps to reproduce the problem (if applicable)
- Expected behavior and actual behavior
- Screenshots (if they help illustrate the issue)

### Submitting Code

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Code Style

- For Python code, please follow the PEP 8 style guide
- For JavaScript/HTML/CSS, use 2 space indentation
- Ensure your code has appropriate comments

### Adding Support for New Schools

If you want to add support for a new school, please follow these steps:

1. Create a new folder in the `backend/school` directory, named after the school
2. Implement the `*_client.py` file in the newly created folder, inheriting from the `BaseAcademicSystemClient` class
3. Implement all necessary methods, including authentication, retrieving course and exam information, etc.
4. Add the new school option to the school selection dropdown menu in the `web/index.html` file

### Testing

- Before submitting a PR, make sure all existing tests pass
- If you add new features, please write corresponding tests for them

Thank you for your contribution to the project!
