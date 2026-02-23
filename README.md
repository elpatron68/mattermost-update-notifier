# Mattermost Update Notifier

An automatic update notifier for Mattermost instances with web admin interface.

**[🇩🇪 German Version](README_de.md)**

## Features

- 🔄 Automatic Mattermost update checking
- 💬 Mattermost webhook notification
- 🌐 Web admin interface for instance management
- 📊 Dashboard with status overview
- 🔐 Password-based authentication
- 🐳 Docker support with docker compose
- 📱 Responsive design
- 🌍 Multi-language support (German/English)

## Screenshots

### Dashboard
![Dashboard](assets/en_mattermost_update_notifier_webapp_main.png)

### Instance Management
![Instance Management](assets/en_mattermost_update_notifier_webapp_instance-management.png)

### Add New Instance
![Add New Instance](assets/en_mattermost_update_notifier_webapp_new-instance.png)

## Installation

### Prerequisites

- Docker and Docker Compose
- At least one Mattermost instance with API access
- Incoming webhook for notifications

### Quick Start

#### Option 1: Using Pre-built Docker Image (Recommended)

1. **Pull and run the image:**
   ```bash
   # GitHub Container Registry (ghcr.io)
   docker pull ghcr.io/elpatron68/mattermost-update-notifier:latest
   
   # Or Docker Hub
   docker pull elpatronki/mattermost-update-notifier:latest
   
   # Run with docker
   docker run -d \
     --name mattermost-update-notifier \
     -p 5000:5000 \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/config.env:/app/config.env \
     ghcr.io/elpatron68/mattermost-update-notifier:latest
   ```

2. **Open web interface:**
   Open http://localhost:5000 in your browser

#### Option 2: Build from Source

1. **Clone repository:**
   ```bash
   git clone https://github.com/elpatron68/mattermost-update-notifier.git
   cd mattermost-update-notifier
   ```

2. **Configure settings:**
   ```bash
   cp config.env.example config.env
   # Edit config.env with your settings
   ```

3. **Start services:**
   ```bash
   # Start web interface only
   docker compose up webapp

   # Or all services (web interface + update checker)
   docker compose --profile checker up
   ```

4. **Open web interface:**
   Open http://localhost:5000 in your browser

## Configuration

### config.env

```bash
# Web Interface Configuration
WEB_PORT=5000
ADMIN_PASSWORD=admin123

# Check Interval (in seconds)
CHECK_INTERVAL=1800
```

### Adding Instances

1. Log in to the web interface
2. Go to "Instances" → "New Instance"
3. Fill in the fields:
   - **Name:** Unique name for the instance
   - **API URL:** `https://your-domain.com/api/v4/config/client?format=old`
   - **Webhook URL:** Incoming webhook URL from Mattermost
   - **Channel:** (Optional) Specific channel for notifications

### Setting up Webhook in Mattermost

1. Go to your Mattermost → System Console → Integrations
2. Enable "Enable Incoming Webhooks"
3. Go to a channel → Channel Info → Integrations
4. Click "Incoming Webhooks" → "Add Incoming Webhook"
5. Copy the generated webhook URL

## Docker Images

Images are published automatically on push to `main` and on releases:

| Registry | Image |
|----------|-------|
| **GitHub Container Registry** | `ghcr.io/elpatron68/mattermost-update-notifier` |
| **Docker Hub** | `elpatronki/mattermost-update-notifier` |

## Docker Services

### Web Interface (Default)
```bash
docker compose up webapp
```
Starts only the web admin interface.

### Update Checker
```bash
docker compose --profile checker up
```
Starts both the web interface and the automatic update checker.

## API Endpoints

- `GET /` - Dashboard
- `GET /instances` - Instance management
- `POST /instances/add` - Add new instance
- `POST /instances/delete/<id>` - Delete instance
- `GET /api/status` - JSON status of all instances

## Development

### Local Development

1. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start services:**
   ```bash
   # Web interface
   python webapp.py

   # Update checker
   python main.py
   ```

### Project Structure

```
mm_update-notifier/
├── main.py              # Update checker script
├── webapp.py            # Flask web interface
├── requirements.txt     # Python dependencies
├── config.env          # Configuration
├── docker-compose.yml  # Docker services
├── Dockerfile          # Docker image
├── data/               # Data directory
│   ├── instances.json  # Instance configuration
│   └── lastnotifiedversion*.txt
└── templates/          # HTML templates
    ├── base.html
    ├── login.html
    ├── dashboard.html
    ├── instances.html
    └── add_instance.html
```

## Troubleshooting

### Common Issues

1. **"API is not reachable"**
   - Check the API URL
   - Ensure the Mattermost instance is accessible

2. **"Version field not found in API response"**
   - Verify the API URL is correct
   - Ensure the `?format=old` parameter is included

3. **Webhook errors**
   - Check the webhook URL
   - Ensure incoming webhooks are enabled

### View Logs

```bash
# Docker logs
docker compose logs -f webapp
docker compose logs -f update-checker

# Local logs
# Logs are displayed in the console
```

### Finding the GHCR Package

To find and manage the Docker image on GitHub Container Registry:

1. Go to your GitHub profile: **https://github.com/elpatron68**
2. Click the **Packages** tab (next to Repositories)
3. Click **mattermost-update-notifier**
4. To make it public: **Package settings** (right sidebar) → **Change visibility** → **Public**

### 403 Forbidden when pushing to GHCR

If the workflow fails with `403 Forbidden` when pushing to ghcr.io, the package exists but is not linked to the repository:

1. Go to **https://github.com/elpatron68** → **Packages** → **mattermost-update-notifier**
2. Click **Package settings** (right sidebar)
3. Under **Manage Actions access**, click **Add repository**
4. Select **elpatron68/mattermost-update-notifier** and grant **Admin** or **Write** access
5. Re-run the workflow

## Security

- Change the default password in `config.env`
- Use HTTPS in production
- Restrict network access to the web interface
- Regular updates of dependencies

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues or questions, please create an issue in the repository.