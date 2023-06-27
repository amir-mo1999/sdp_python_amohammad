## Setup
# Docker Setup
1. Download repository
2. Start Docker Desktop
3. Run: `docker-compose build`
4. Run: `docker-compose up`
5. Open dashboard under: [127.0.0.1:5000](http://127.0.0.1:5000/)

# Local Setup
1. In the Frontend directory create an .env file with following variables:
   - `BACKEND_HOST=Backend`
   - `BACKEND_PORT=5000`
2. In the Backend directory run: `python wsgi.py`
3. In the Frontend directory run: `python wsgi.py`
5. Open dashboard under: [127.0.0.1:5000](http://127.0.0.1:5000/)

