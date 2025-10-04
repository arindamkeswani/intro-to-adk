# Prerequisites: 
1. Install python
2. Have an IDE

Steps:
1. Set up the python environment

- Initialize .vnev `python -m venv .venv`/`python3 -m venv .venv`

- Activate virtual env

    - Activate (each new terminal)

    - macOS/Linux: source .venv/bin/activate

    - Windows CMD (Git Bash): source .venv/Scripts/activate

    - Windows PowerShell: .venv\Scripts\Activate.ps1


2. `pip install -r requirements.txt`/`pip3 install -r requirements.txt`

3. Have the following project structure
```
parent_folder/
    multi_tool_agent/
        __init__.py
        agent.py
        .env
```
4. Defined root agent and start integrating tools and services!
5. Run project with `adk web`

Note: ElevenLabs integration will need ffmpeg
1. Download ffmpeg from here: https://ffmpeg.org/download.html#build-windows
2. Choose build, install via CLI: `winget install ffmpeg`
4. Check installation via command line: ffmpeg -version
5. Add ffmpeg to scripts
- `where ffmpeg` to get installation folder
- Copy files to Scripts folder

# Deployment

## Google Cloud CLI set-up
- Install CLI ([docs](https://cloud.google.com/sdk/docs/install-sdk))
- Init CLI & Set required project

## Local actions
- Install UX ([docs](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer))
- Go to project root & run `uvx agent-starter-pack enhance --adk -d agent_engine`

## GCP & Vertex AI Set-up
- Create Project on GCP
- Enable Vertex AI APIs
- Create Bucket
<!-- - Copy Project ID, bucket, location in depl -->

## Deployment
- Follow [docs](https://google.github.io/adk-docs/deploy/agent-engine/#deploy-ad)
- Go to Project Root (folder in which a specific agent logic can be found)
- Note: Terraform should be installed for this step
- `make setup-dev-env` - This creates a developer environment
- `make backend`

## Testing
- Get Query URL from Agent Engine page

Link to generate Reddit API Key: https://www.reddit.com/prefs/apps/

TODO: Add Video Tutorial Links