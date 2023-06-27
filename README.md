## Setup
### Docker Setup
1. Download repository
2. Start Docker Desktop
3. Run: `docker-compose build`
4. Run: `docker-compose up`
5. Open dashboard under: [127.0.0.1:5000](http://127.0.0.1:5000/)

### Local Setup
1. Download repository
2. In the Frontend directory create an .env file with following variables:
   - `BACKEND_HOST=Backend`
   - `BACKEND_PORT=5000`
3. Create two environments for the backend and frontend directories respectively using the respective requirements.txt files
4. Run the command `python wsgi.py` in the backend directory within its respective virtual env and proceed analogically in the frontend directory
5. Open dashboard under: [127.0.0.1:5000](http://127.0.0.1:5000/)

