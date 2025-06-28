# 🌱 Khadra: Reforesting Algeria, One Tree at a Time


Khadra is a Django-powered web application for an Algerian non-profit organization dedicated to reforesting Algeria. Our platform connects volunteers with tree-planting initiatives across the country, making it easy to participate in environmental restoration efforts.

## 🌟 Features

- **Interactive Tree Map**: Visualize planting locations using PostGIS spatial data
- **Volunteer Dashboard**: Track your contributions and upcoming events
- **Real-time Notifications**: Get alerts about new planting projects
- **Progress Tracking**: See total trees planted with dynamic counters
- **Project Participation**: Join planting initiatives with one click

## 🛠️ Technology Stack

**Backend**  
![Django](https://img.shields.io/badge/Django-092E20?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?logo=postgresql&logoColor=white)
![PostGIS](https://img.shields.io/badge/PostGIS-336791?logo=postgis&logoColor=white)

**Frontend**  
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript&logoColor=black)
![Bootstrap](https://img.shields.io/badge/Bootstrap-7952B3?logo=bootstrap&logoColor=white)
![Leaflet](https://img.shields.io/badge/Leaflet-199900?logo=leaflet&logoColor=white)

**Infrastructure**  
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?logo=github-actions&logoColor=white)

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- PostgreSQL 12+ with PostGIS extension
- Redis (for caching and async tasks)

### Installation
```bash
# Clone the repository
git clone https://github.com/TonyXdZ/khadra.git

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Docker Setup
```bash
docker-compose up --build
```

## 🗺️ Project Structure

```
khadra/
├── core/               # Main app configuration
├── users/           # User authentication & profiles
├── plantations/        # Tree planting projects management
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

1. **User Registration & Profiles**
   - Volunteer signup with email verification
   - Personalized dashboard showing participation history
   - Notification preferences management

2. **Interactive Planting Map**
   - Visualize all planting locations with Leaflet.js
   - Cluster visualization for dense planting areas

3. **Project Management**
   - Organization staff can create new planting initiatives
   - Set volunteer capacity and required equipment
   - Automatic notifications to nearby volunteers

4. **Impact Tracking**
   - Real-time counter of total trees planted
   - Regional statistics and environmental impact metrics
   - Volunteer leaderboards and achievements


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

For inquiries about the project or partnership opportunities:

- Email: ayoubencherif23@gmail.com

---

**Together, let's make Algeria green again!** 🌳🇩🇿