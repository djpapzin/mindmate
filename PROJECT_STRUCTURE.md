# MindMate Project Structure

## Directory Organization

```
mindmate/
├── src/                    # Source code
│   └── bot.py             # Main bot application
├── config/                 # Configuration files
│   └── .env.example       # Environment variables template
├── logs/                   # Log files
│   └── bot.log            # Bot runtime logs
├── scripts/                # Utility scripts
│   └── test_bot.py        # Bot testing script
├── docs/                   # Documentation
│   ├── PERSONAL_MODE_UPDATE.md
│   └── other docs...
├── research/               # Research and analysis
│   └── various research files
├── .windsurf/             # IDE configuration
├── .git/                  # Git repository
├── .env                   # Environment variables (local)
├── .gitignore            # Git ignore rules
├── Procfile              # Heroku/Render deployment config
├── render.yaml           # Render deployment config
├── requirements.txt      # Python dependencies
└── README.md            # Project documentation
```

## File Purposes

### Core Application
- **src/bot.py**: Main Telegram bot application with Personal Mode features

### Configuration
- **config/.env.example**: Template for environment variables
- **.env**: Local environment variables (not committed)
- **requirements.txt**: Python package dependencies

### Deployment
- **Procfile**: Tells Render how to run the application
- **render.yaml**: Render-specific configuration

### Documentation
- **docs/**: All project documentation
- **README.md**: Main project README
- **ROADMAP.md**: Project roadmap and planning

### Utilities
- **scripts/**: Helper scripts and utilities
- **logs/**: Runtime logs (for local development)

### Research
- **research/**: Analysis, AB test results, and research notes

## Development Workflow

1. **Main development**: Work in `src/bot.py`
2. **Testing**: Use `scripts/test_bot.py`
3. **Configuration**: Copy `config/.env.example` to `.env` and fill in values
4. **Documentation**: Update docs in `docs/` directory
5. **Deployment**: Push to GitHub, Render auto-deploys from main branch

## Environment Setup

1. Copy environment template:
   ```bash
   cp config/.env.example .env
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run locally:
   ```bash
   python src/bot.py
   ```

## Notes

- The `.env` file should never be committed to version control
- Log files are kept in `logs/` for local development
- All documentation lives in `docs/` for better organization
- Scripts and utilities are in `scripts/` to keep root directory clean
