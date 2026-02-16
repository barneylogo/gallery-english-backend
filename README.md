# Micro Gallery Japan - Backend API

FastAPI backend for the artwork marketplace platform.

## Features

- ✅ FastAPI framework with async support
- ✅ Supabase integration (Auth, Database, Storage)
- ✅ Redis caching and job queues
- ✅ AI/ML endpoints for space analysis and recommendations
- ✅ Image processing capabilities
- ✅ Auto-generated API documentation (Swagger/OpenAPI)
- ✅ Docker support
- ✅ Comprehensive testing suite

## Tech Stack

- **Framework**: FastAPI 0.104+
- **Language**: Python 3.10+
- **Database**: Supabase PostgreSQL
- **Auth**: Supabase Auth
- **Storage**: Supabase Storage
- **Cache**: Redis
- **Queue**: Celery
- **ML/AI**: PyTorch, OpenCV, scikit-learn

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/     # API endpoints
│   │       └── router.py      # Main router
│   ├── core/                  # Core configuration
│   │   ├── config.py          # Settings
│   │   ├── supabase.py        # Supabase client
│   │   └── redis_client.py    # Redis client
│   ├── models/                # Pydantic models
│   ├── services/              # Business logic
│   ├── ml/                    # AI/ML models
│   ├── utils/                 # Utilities
│   └── main.py                # FastAPI app
├── tests/                     # Test suite
├── logs/                      # Application logs
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose
└── .env.example               # Environment variables template
```

## Getting Started

### Prerequisites

- Python 3.10+
- Redis (optional, for local development)
- Supabase account

### Installation

1. **Clone the repository** (if not already done)

2. **Navigate to backend directory**
```bash
cd backend
```

3. **Create virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

5. **Setup environment variables**
```bash
cp .env.example .env
```

Edit `.env` and add your Supabase credentials:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon key
- `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key
- `SECRET_KEY`: Generate a secure secret key

6. **Run the development server**
```bash
python -m uvicorn app.main:app --reload
```

The API will be available at:
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## Docker Setup

### Using Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Using Docker only

```bash
# Build image
docker build -t mgj-api .

# Run container
docker run -p 8000:8000 --env-file .env mgj-api
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_main.py
```

## Development

### Adding New Endpoints

1. Create endpoint file in `app/api/v1/endpoints/`
2. Define routes using FastAPI decorators
3. Add router to `app/api/v1/router.py`

Example:
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/example")
async def example_endpoint():
    return {"message": "Hello World"}
```

### Environment Variables

All configuration is managed through `.env` file. See `.env.example` for all available options.

### Database Migrations

TODO: Add Alembic migration instructions

## API Endpoints

### Authentication (`/api/v1/auth`)
- `POST /signup` - User registration
- `POST /login` - User login
- `POST /logout` - User logout

### Users (`/api/v1/users`)
- `GET /me` - Get current user profile
- `PUT /me` - Update user profile

### Artworks (`/api/v1/artworks`)
- `GET /` - List artworks
- `GET /{id}` - Get artwork details
- `POST /` - Create artwork

### Spaces (`/api/v1/spaces`)
- `GET /` - List spaces
- `GET /{id}` - Get space details
- `POST /` - Create space

### AI/ML (`/api/v1/ai`)
- `POST /analyze-space` - Analyze space image
- `POST /recommend-artworks` - Get artwork recommendations
- `POST /upload-space-image` - Upload space image

## Deployment

### Production Checklist

- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Set `DEBUG=False`
- [ ] Generate secure `SECRET_KEY`
- [ ] Configure CORS origins
- [ ] Setup Sentry for monitoring
- [ ] Enable Redis for caching
- [ ] Setup SSL/TLS certificate
- [ ] Configure database connection pooling

### Deployment Options

- **Google Cloud Run** (Recommended)
- **AWS Lambda** with Mangum adapter
- **Railway**
- **Render**
- **Fly.io**

## Contributing

1. Create a feature branch
2. Make your changes
3. Write tests
4. Run tests and linting
5. Submit pull request

## License

Proprietary - Micro Gallery Japan

## Support

For questions or issues, please contact the development team.
