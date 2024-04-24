from flask import Blueprint

# Import your controllers here
from .jiracontroller import jira_bp
from .linkedincontroller import linkedin_bp
from .githubcontroller import github_bp
from .employeecontroller import employeecontroller
from .skillcontroller import skill_bp
from .skilldatasetcontroller import skilldataset_bp

# Register your blueprints here
controllers_bp = Blueprint('controllers', __name__)

# Register the jira, linkedin, and github blueprints
controllers_bp.register_blueprint(jira_bp)
controllers_bp.register_blueprint(linkedin_bp)
controllers_bp.register_blueprint(github_bp)
controllers_bp.register_blueprint(employeecontroller)
controllers_bp.register_blueprint(skill_bp)
controllers_bp.register_blueprint(skilldataset_bp)