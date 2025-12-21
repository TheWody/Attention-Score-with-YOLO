import requests

response = requests.post(
    "http://localhost:5001/api/auth/register",
    json={
        "name": "Yusuf Murat ERTEN",
        "email": "yusufmurat.erten@university.edu",
        "password": "test123",
        "department": "Computer Engineering"
    }
)

if response.status_code == 201:
    print("✓ Generated!")
    print("Email: yusufmurat.erten@university.edu")
    print("Password: test123")
else:
    print("Hata:", response.json())

login_response = requests.post(
    "http://localhost:5001/api/auth/login",
    json={
        "email": "yusufmurat.erten@university.edu",
        "password": "test123"
    }
)

if login_response.status_code == 200:
    token = login_response.json()['token']

    course_response = requests.post(
        "http://localhost:5001/api/courses",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "course_code": "EEE 302",
            "course_name": "Digital Signal Processing",
            "classroom_location": "A-201",
            "semester": "2024 Spring"
        }
    )

    if course_response.status_code == 201:
        print("✓ Ders generated: EEE 302")
    else:
        print("Error:", course_response.json())