# Literature Review Assistant

A Streamlit application for analyzing academic papers using AI.

## Project Structure
```
literature_review_assistant/
├── app/
│   ├── __init__.py
│   └── main.py              # Main Streamlit application
├── config/
│   ├── __init__.py
│   ├── config.yaml          # API configuration (not in git)
│   └── config.yaml.example  # Example configuration
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Quick Deployment

1. Clone the repository:
```bash
git clone <repository-url>
cd literature_review_assistant
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up configuration:
```bash
cp config/config.yaml.example config/config.yaml
# Edit config/config.yaml with your API settings
```

5. Run the application:
```bash
streamlit run app/main.py
```

## Configuration

Edit `config/config.yaml` with your settings:
```yaml
api:
  base_url: "your-api-endpoint"
  key: "your-api-key"
model:
  alias: "claude-v4-sonnet"
```

## Production Deployment

For production deployment:

1. Ensure all dependencies are installed
2. Configure your API settings in `config/config.yaml`
3. Use a process manager (like PM2) to run the Streamlit app
4. Set up a reverse proxy (like Nginx) if needed

## Security Notes

- Never commit `config.yaml` to version control
- Keep your API key secure
- Use environment variables in production if possible
- Regularly update dependencies

## Requirements

- Python 3.8+
- Streamlit
- See requirements.txt for full list 