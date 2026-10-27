REQUEST_VALIDATION_FAILED = "Request validation failed"
SERVICE_UNAVAILABLE = "Service unavailable"
DATABASE_READINESS_FAILED = "Database readiness probe failed"

CORS_EXPLICIT_ORIGINS_REQUIRED = "CORS_ALLOWED_ORIGINS must list explicit origins"
CORS_HTTP_ORIGINS_REQUIRED = "CORS_ALLOWED_ORIGINS must contain only HTTP(S) origins"

CLI_DESCRIPTION = "TaskHub operator commands"
CLI_CREATE_ADMIN_HELP = "Create a new active administrator"
CLI_SEED_HELP = "Create demo data for an existing active user"
CLI_OWNER_HELP = "Existing owner's username"
CLI_PASSWORD_PROMPT = "Password: "
CLI_PASSWORD_CONFIRM_PROMPT = "Confirm password: "
CLI_PASSWORD_MISMATCH = "Passwords do not match."
CLI_ADMIN_CREATED = "Created administrator '{username}' (id={id})."
CLI_DEMO_READY = "Demo data is ready."
CLI_VALIDATION_ERROR = "{field}: {message}"
CLI_DATABASE_FAILED = "Database operation failed. Check connectivity and migrations."
CLI_CANCELLED = "Command cancelled."

PROJECT_NOT_FOUND = "Project not found"
PROJECT_OWNER_NOT_FOUND = "Project owner not found"
PROJECT_NAME_CANNOT_BE_NULL = "name cannot be null"

USER_NOT_FOUND = "User not found"
DUPLICATE_USER = "Username or email already exists"
INVALID_CREDENTIALS = "Invalid username or password"
CREDENTIALS_COULD_NOT_BE_VALIDATED = "Could not validate credentials"
ACCOUNT_INACTIVE = "This account is inactive"
ADMIN_REQUIRED = "Administrator access is required"
PROJECT_MANAGER_REQUIRED = "Project manager access is required"

TASK_ASSIGNEE_NOT_FOUND = "Assignee not found"
TASK_TAGS_INVALID = "One or more tag_ids are invalid"
TASK_NOT_FOUND = "Task not found"
TASK_BOOKMARK_NOT_FOUND = "Task bookmark not found"
TASK_COMMENT_NOT_FOUND = "Task comment not found"
TASK_COMMENT_AUTHOR_REQUIRED = (
    "Only the comment author, an administrator, or the project owner may change it"
)

DUPLICATE_TAG = "Tag name already exists"
