# Sbuga Sonolus Server

Sbuga's Sonolus Server to play PJSK official charts.

## Setup

### required stuff

- Python 3.10+
- Redis
- MeCab dictionary for cutlet (Japanese romanization)
- PSQL
- S3 server
- sbuga-backend server API (also requires a S3 server)

### dependencies

note: needs git-cli (git-scm) for git+ installs

```bash
pip install -r requirements.txt
python -m unidic download
```

The `unidic download` step is required for `cutlet` (Japanese romanization). It downloads the MeCab dictionary (~500MB).

### config

Switch config using `python main.py -c config.file`

### Engine Resources
Place engine, skin, effect, particle, and background files in `files/`.
