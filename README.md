# 🌱 Khadra: Reforesting Algeria, One Tree at a Time

<div align="center" style="background-color:#e6f7e6; padding:20px; border-radius:10px; margin-bottom:30px;">
  <h3>🎨 Designers Wanted!</h3>
  <p>We're looking for talented designers to create a <strong>brand identity and logo</strong> for Khadra!</p>
  <p>If you'd like to contribute your design skills to our environmental cause, please reach out at:</p>
  <p>📧 <strong>khadra.devs@gmail.com</strong></p>
  <p>Your work will be seen by thousands of volunteers helping reforest Algeria!</p>
</div>

Khadra is a Django-powered web application for an Algerian non-profit organization dedicated to reforesting Algeria. Our platform connects volunteers with tree-planting initiatives across the country, making it easy to participate in environmental restoration efforts.

## 🌟 Features

- **Manager Approval System**: New initiatives require manager reviews before activation
- **Role Promotion Workflow**: Volunteers can request manager status, subject to approval by existing managers
- **Review Period**: 7-day voting window for both new initiatives AND role promotion requests
- **Automated Evaluation System**: Celery tasks handle:
  - Initiative lifecycle transitions (status changes)
  - Role promotion request evaluations
- **Interactive Tree Map**: Visualize planting locations using PostGIS spatial data
- **Volunteer Dashboard**: Track your contributions and upcoming events
- **Real-time Notifications**: Get alerts about new projects, role changes, and voting outcomes
- **Project Participation**: Join planting initiatives with one click

## 🛠️ Technology Stack

**Backend**  
![Django](https://img.shields.io/badge/Django-092E20?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?logo=postgresql&logoColor=white)
![PostGIS](https://img.shields.io/badge/PostGIS-336791?logo=postgis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A?logo=celery&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)

**Frontend**  
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript&logoColor=black)
![Bootstrap](https://img.shields.io/badge/Bootstrap-7952B3?logo=bootstrap&logoColor=white)
![Leaflet](https://img.shields.io/badge/Leaflet-199900?logo=leaflet&logoColor=white)

**Infrastructure**  
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Docker_Compose-2496ED?logo=docker&logoColor=white)

## 🚀 Getting Started (Docker Recommended)

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Docker Setup
```bash
# Clone the repository
git clone https://github.com/TonyXdZ/khadra.git
cd khadra

# Build and start all services
docker-compose up --build

# Access the application at:
http://localhost:8000
```

### First-time Setup
After starting the containers:
```bash
# Create superuser (required for admin access)
docker-compose exec web python manage.py createsuperuser

# Collect static files (if not already done by entrypoint)
docker-compose exec web python manage.py collectstatic --no-input
```

### How It Works
The system uses an entrypoint script that:
1. Waits for PostgreSQL and Redis to become available
2. Runs database migrations automatically
3. Starts the Django application server

Here's what happens during startup:
```
[Entrypoint Script]
├── Wait for PostgreSQL (db:5432) ✅
├── Wait for Redis (redis:6379) ✅
├── Run database migrations
└── Start server (gunicorn)
```

### Important Notes
1. The entrypoint script automatically handles database migrations on every startup
2. You only need to create a superuser once (first setup)
3. Static files are collected automatically during build
4. To stop the system: `docker-compose down`

## 🔄 Background Tasks (Celery)

Khadra uses Celery for asynchronous task processing. Key tasks include:

### Initiative Review Workflow

1. **Manager Notification**: Managers receive notifications when new initiatives are created
2. **7-Day Review Period**: Managers have 7 days to vote on new initiatives
3. **Approval Threshold**: Requires minimum votes (`MIN_INITIATIVE_REVIEWS_REQUIRED`) and majority approval

### Task Documentation

```python
@shared_task
def evaluate_initiative_reviews_task(initiative_id):
    """
    Evaluates initiative review outcomes after the 7-day review period
    - Checks for minimum required reviews
    - Tallys approve/reject votes
    - Transitions status:
        • 'review_failed' - Insufficient votes or majority rejection
        • 'upcoming' - Approved by managers
    - Sends approval/rejection notifications
    - Schedules future status transitions
    """
    ...

@shared_task
def transition_initiative_to_ongoing_task(initiative_id):
    """
    Transitions initiative to 'ongoing' status at scheduled start time
    - Only transitions if status is 'upcoming'
    - Sends initiative-started notifications
    """
    ...

@shared_task
def transition_initiative_to_completed_task(initiative_id):
    """
    Transitions initiative to 'completed' status at calculated end time
    - Handles both 'ongoing' and delayed 'upcoming' initiatives
    - Sends completion notifications
    """
    ...
```

### Initiative Lifecycle Flowchart
```
[New Initiative Created]
        ↓
[Notify Managers] → [7-Day Review Period]
        ↓
evaluate_initiative_reviews_task()
        ├── Approved → Status: 'upcoming'
        │       ├── Schedule → transition_initiative_to_ongoing_task()
        │       └── Schedule → transition_initiative_to_completed_task()
        │
        └── Rejected → Status: 'review_failed'
```

## 🗺️ Project Structure

```
khadra/
├── core/               # Main app with initiative management
│   ├── tasks/          # Celery task definitions for initiatives
│   └── ...             # Other core functionality
├── users/              # User authentication & profiles
│   ├── tasks/          # Celery task definitions for user management
│   └── ...             # Other user functionality
├── notifications/      # User notification system
├── geodata/            # Spatial data and mapping functionality
├── static/             # CSS, JS, and images
├── templates/          # HTML templates
├── manage.py
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 🌲 Key Functionality

### Initiative Management
- **Manager Approval**: New initiatives require manager consensus
- **Review Voting**: Managers approve/reject during 7-day window
- **Automated Transitions**:
  - `upcoming` → `ongoing` at scheduled start time
  - `ongoing` → `completed` after duration ends
- **Status Tracking**:
  - `review_pending`: Waiting for manager votes
  - `review_failed`: Rejected or insufficient votes
  - `upcoming`: Approved, not yet started
  - `ongoing`: Currently active
  - `completed`: Finished initiative

### User System
- **Role-Based Access**:
  - All new users start as `Volunteers`
  - Volunteers can request manager status through promotion requests
- **Account Lifecycle**:
  - Volunteer signup with email verification
  - *(Future: Social login via Google/Facebook)*
  - Manager promotion workflow:
    1. Volunteer submits promotion request
    2. Existing managers vote during 7-day window
    3. Automated approval/rejection based on voting consensus
- **Privileges**:
  - Volunteers: Participate in initiatives, track contributions
  - Managers: Approve/reject new initiatives AND promotion requests
- Personalized dashboard showing:
  - Participation history
  - Current promotion request status
  - Pending votes (for managers)

## 🤝 How to Contribute

We welcome contributions from developers passionate about environmental conservation!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a pull request

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0** - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

For inquiries about the project, partnership opportunities, or design contributions:
- Email: khadra.devs@gmail.com

---

**Together, let's make Algeria green again!** 🌳🇩🇿