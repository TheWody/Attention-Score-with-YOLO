# Attention Score with YOLO

Classroom attention monitoring system using YOLO pose estimation and emotion detection.

## Project Structure

```
Attention-Score-with-YOLO/
├── client/                    # Client (Teacher) application
│   ├── __init__.py
│   ├── api_client.py         # Server communication
│   ├── config.json           # Client configuration
│   └── gui/
│       ├── __init__.py
│       ├── main_window.py    # Main monitoring window
│       └── login_window.py   # Login & registration
│
├── server/                    # Server (Dashboard) application
│   ├── __init__.py
│   ├── app.py                # Flask app with all routes
│   └── templates/
│       └── dashboard.html
│
├── core/                      # Shared analysis modules
│   ├── __init__.py
│   ├── yolo_model.py         # YOLO pose & emotion detection
│   ├── attention_analyzer.py # Attention score calculation
│   ├── camera_manager.py     # Camera feed handling
│   └── lesson_report.py      # Lesson report generation
│
├── models/                    # YOLO model files
│   ├── yolov8n-pose.pt
│   └── yolov8n-cls.pt
│
├── scripts/                   # Startup scripts
│   ├── StartClient.bat       # Windows client starter
│   ├── StartClient.sh        # Mac/Linux client starter
│   ├── StartDashboard.bat    # Windows server starter
│   └── StartDashboard.sh     # Mac/Linux server starter
│
├── main.py                    # Client entry point
├── run_server.py             # Server entry point
├── create_admin.py           # Admin user creation utility
└── requirements.txt
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server (Dashboard)
```bash
# Windows
scripts\StartDashboard.bat

# Mac/Linux
./scripts/StartDashboard.sh
```

Dashboard: http://localhost:5001/dashboard

**Default Admin:**
- Username: `admin`
- Password: `admin123`

### 3. Start the Client (Teacher App)
```bash
# Windows
scripts\StartClient.bat

# Mac/Linux
./scripts/StartClient.sh
```

## Features

- **Real-time Attention Monitoring**: Uses YOLO pose estimation to detect student attention
- **Emotion Detection**: Analyzes facial expressions for engagement metrics
- **Teacher Dashboard**: Login, register, and manage courses
- **Admin Dashboard**: View all lessons and statistics
- **Lesson Reports**: Automatic HTML report generation with charts

## Configuration

### Client Configuration (`client/config.json`)
```json
{
    "server_url": "http://localhost:5001",
    "version": "1.0.0"
}
```

For remote server, change `localhost` to the server's IP address.

## Building Executables

```bash
# Build both client and server executables
scripts\build_exe.bat
```

## License

MIT License

