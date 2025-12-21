import requests
from typing import Optional, Dict, List
import json


class APIClient:
    """Server ile iletişim kuran API client."""

    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.teacher_info: Optional[Dict] = None

    def _get_headers(self) -> Dict:
        """Request header'larını döndürür."""
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers

    def login(self, email: str, password: str) -> bool:
        """Hoca girişi yapar."""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json={'email': email, 'password': password},
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data['token']
                self.teacher_info = data['teacher']
                print(f"Giriş başarılı: {self.teacher_info['name']}")
                return True
            else:
                print(f"Giriş başarısız: {response.json().get('message', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"Login error: {e}")
            return False

    def register(self, name: str, email: str, password: str, department: str = "") -> bool:
        """Yeni hoca kaydı oluşturur."""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/register",
                json={
                    'name': name,
                    'email': email,
                    'password': password,
                    'department': department
                },
                headers={'Content-Type': 'application/json'}
            )

            return response.status_code == 201
        except Exception as e:
            print(f"Register error: {e}")
            return False

    def get_courses(self) -> List[Dict]:
        """Hoca'nın derslerini getirir."""
        try:
            response = requests.get(
                f"{self.base_url}/api/courses",
                headers=self._get_headers()
            )

            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Get courses error: {e}")
            return []

    def create_course(self, course_code: str, course_name: str,
                      classroom_location: str = "", semester: str = "") -> Optional[int]:
        """Yeni ders oluşturur."""
        try:
            response = requests.post(
                f"{self.base_url}/api/courses",
                json={
                    'course_code': course_code,
                    'course_name': course_name,
                    'classroom_location': classroom_location,
                    'semester': semester
                },
                headers=self._get_headers()
            )

            if response.status_code == 201:
                return response.json()['course_id']
            return None
        except Exception as e:
            print(f"Create course error: {e}")
            return None

    def start_session(self, course_id: int) -> Optional[int]:
        """Yeni session başlatır."""
        try:
            response = requests.post(
                f"{self.base_url}/api/sessions/start",
                json={'course_id': course_id},
                headers=self._get_headers()
            )

            if response.status_code == 201:
                session_id = response.json()['session_id']
                print(f"Session başlatıldı: {session_id}")
                return session_id
            return None
        except Exception as e:
            print(f"Start session error: {e}")
            return None

    def save_minute_metric(self, session_id: int, minute_number: int,
                           avg_score: float, min_score: int, max_score: int,
                           avg_attentive: int, avg_distracted: int) -> bool:
        """Dakikalık metriği server'a gönderir."""
        try:
            response = requests.post(
                f"{self.base_url}/api/sessions/{session_id}/minute",
                json={
                    'minute_number': minute_number,
                    'avg_score': avg_score,
                    'min_score': min_score,
                    'max_score': max_score,
                    'avg_attentive': avg_attentive,
                    'avg_distracted': avg_distracted
                },
                headers=self._get_headers()
            )

            if response.status_code == 201:
                print(f"Dakika {minute_number} metriği kaydedildi")
                return True
            return False
        except Exception as e:
            print(f"Save minute metric error: {e}")
            return False

    def end_session(self, session_id: int, duration_seconds: int,
                    avg_attention_score: float, peak_score: int,
                    total_students: int) -> Optional[float]:
        """Session'ı sonlandırır."""
        try:
            response = requests.post(
                f"{self.base_url}/api/sessions/{session_id}/end",
                json={
                    'duration_seconds': duration_seconds,
                    'avg_attention_score': avg_attention_score,
                    'peak_score': peak_score,
                    'total_students': total_students
                },
                headers=self._get_headers()
            )

            if response.status_code == 200:
                result = response.json()
                print(f"Session sonlandırıldı - Avg Score: {result['avg_attention_score']}")
                return result['avg_attention_score']
            return None
        except Exception as e:
            print(f"End session error: {e}")
            return None

    def get_sessions(self, course_id: Optional[int] = None) -> List[Dict]:
        """Session'ları getirir."""
        try:
            params = {'course_id': course_id} if course_id else {}
            response = requests.get(
                f"{self.base_url}/api/sessions",
                params=params,
                headers=self._get_headers()
            )

            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Get sessions error: {e}")
            return []

    def get_session_detail(self, session_id: int) -> Optional[Dict]:
        """Session detaylarını getirir."""
        try:
            response = requests.get(
                f"{self.base_url}/api/sessions/{session_id}",
                headers=self._get_headers()
            )

            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Get session detail error: {e}")
            return None

    def get_dashboard_stats(self) -> Optional[Dict]:
        """Dashboard istatistiklerini getirir."""
        try:
            response = requests.get(
                f"{self.base_url}/api/dashboard/stats",
                headers=self._get_headers()
            )

            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Get dashboard stats error: {e}")
            return None