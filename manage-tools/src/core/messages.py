"""Message constants for the application"""

# Tool validation messages
TOOL_NAME_EMPTY = "Tool name cannot be empty"
TOOL_NAME_INVALID_CHARS = "Tool name can only contain letters, numbers, hyphens (-), and underscores (_)"
TOOL_NAME_TOO_LONG = "Tool name must be 64 characters or less"
TOOL_ALREADY_EXISTS = "Tool '{}' already exists"

# Directory validation messages  
DIRECTORY_NOT_FOUND = "Source directory does not exist: {}"
PATH_NOT_DIRECTORY = "Source path is not a directory: {}"

# Tool operation messages
TOOL_NOT_FOUND = "Tool '{}' not found"
TOOL_CREATED = "Tool '{}' created successfully"
TOOL_UPDATED = "Tool '{}' updated successfully"
TOOL_DELETED = "Tool '{}' deleted successfully"
TOOL_ENABLED = "Tool '{}' enabled"
TOOL_DISABLED = "Tool '{}' disabled"