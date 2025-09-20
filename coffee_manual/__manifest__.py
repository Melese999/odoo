{
    "name": "Coffee Manual",
    "summary": "Interactive user manual for the Coffee Management System with progress tracking and quizzes",
    "version": "17.0.1.0.0",
    "category": "Productivity",
    "author": "AMG Business Application",
    "website": "",
    "description": """
        Interactive user manual for the Coffee Management System with progress tracking and quizzes.
    """,
    "depends": ["website", "coffee_management"],

    "data": [
        "security/ir.model.access.csv",
        "data/sections.xml",
        "data/quizzes.xml",
        "views/actions.xml",
        "views/menu.xml", # This file will be modified in the next step
        "views/templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "coffee_manual/static/src/css/manual.css",
            "coffee_manual/static/src/js/manual_scripts.js",  # <-- ADD THIS LINE
        ],
    },    
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}