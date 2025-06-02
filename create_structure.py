import os

# Define the subdirectory and file structure inside affiliate_outreach_system
structure = {
    "alembic": [
        "env.py",
        "script.py.mako",
        "versions/"
    ],
    "api": {
        "__init__.py": "",
        "main.py": "",
        "dependencies.py": "",
        "routers": [
            "__init__.py",
            "prospects.py",
            "templates.py",
            "campaigns.py",
            "health.py"
        ],
        "schemas": [
            "__init__.py",
            "prospect.py",
            "template.py",
            "campaign.py"
        ]
    },
    "services": [
        "__init__.py",
        "email_service.py",
        "scoring_service.py",
        "social_service.py",
        "validator.py"
    ],
    "tasks": [
        "__init__.py",
        "celery_app.py",
        "outreach_tasks.py",
        "scoring_tasks.py"
    ],
    "database": [
        "__init__.py",
        "models.py",
        "session.py"
    ],
    "ui": [
        "__init__.py",
        "gradio_app.py"
    ],
    "tests": {
        "__init__.py": "",
        "test_api": [
            "test_prospects.py",
            "test_templates.py",
            "test_campaigns.py"
        ],
        "test_services": [
            "test_email_service.py",
            "test_scoring_service.py",
            "test_validator.py"
        ],
        "test_tasks": [
            "test_outreach_tasks.py",
            "test_scoring_tasks.py"
        ]
    },
    "config": [
        "__init__.py",
        "settings.py"
    ],
    "static": {
        "css/": [
            "style.css"
        ],
        "js/": [
            "script.js"
        ],
        "images/": [
            "placeholder.png"
        ]
    },
    "templates": [
        "welcome_email.html",
        "follow_up_email.html"
    ],
    "docs": [
        "api.md",
        "setup.md",
        "system_design.md"
    ],
    ".env": "",
    "requirements.txt": "",
    "README.md": "",
    "docker-compose.yml": "",
    "Dockerfile": ""
}

def create_structure(base_path, structure):
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        elif isinstance(content, list):
            os.makedirs(path, exist_ok=True)
            for item in content:
                item_path = os.path.join(path, item)
                if item.endswith("/"):
                    os.makedirs(item_path, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(item_path), exist_ok=True)
                    open(item_path, 'a').close()
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, 'a').close()

if __name__ == "__main__":
    base_dir = "affiliate_outreach_system"
    if not os.path.isdir(base_dir):
        print(f"Directory '{base_dir}' does not exist.")
    else:
        create_structure(base_dir, structure)
        print("Subdirectories and files created inside 'affiliate_outreach_system'.")
