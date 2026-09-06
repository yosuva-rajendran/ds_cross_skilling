"""Constants for change types and severity levels used in version comparison."""

# Severity levels
BREAKING = "breaking"
NON_BREAKING = "non_breaking"
INFORMATIONAL = "informational"

# Endpoint-level change types
ENDPOINT_ADDED = "endpoint_added"
ENDPOINT_REMOVED = "endpoint_removed"

# Parameter change types
PARAMETER_ADDED = "parameter_added"
REQUIRED_PARAMETER_ADDED = "required_parameter_added"
PARAMETER_REMOVED = "parameter_removed"
PARAMETER_TYPE_CHANGED = "parameter_type_changed"
PARAMETER_CONSTRAINT_CHANGED = "parameter_constraint_changed"

# Request body change types
REQUEST_BODY_ADDED = "request_body_added"
REQUEST_BODY_REMOVED = "request_body_removed"
REQUEST_BODY_TYPE_CHANGED = "request_body_type_changed"
REQUEST_BODY_PROPERTY_ADDED = "request_body_property_added"
REQUEST_BODY_REQUIRED_PROPERTY_ADDED = "request_body_required_property_added"
REQUEST_BODY_PROPERTY_REMOVED = "request_body_property_removed"
REQUEST_BODY_PROPERTY_TYPE_CHANGED = "request_body_property_type_changed"

# Response change types
RESPONSE_STATUS_ADDED = "response_status_added"
RESPONSE_STATUS_REMOVED = "response_status_removed"
RESPONSE_SCHEMA_TYPE_CHANGED = "response_schema_type_changed"
RESPONSE_PROPERTY_ADDED = "response_property_added"
RESPONSE_PROPERTY_REMOVED = "response_property_removed"
RESPONSE_PROPERTY_TYPE_CHANGED = "response_property_type_changed"

# Component change types
COMPONENT_ADDED = "component_added"
COMPONENT_REMOVED = "component_removed"
COMPONENT_PROPERTY_ADDED = "component_property_added"
COMPONENT_PROPERTY_REMOVED = "component_property_removed"
COMPONENT_PROPERTY_TYPE_CHANGED = "component_property_type_changed"
COMPONENT_REQUIRED_CHANGED = "component_required_changed"

# Description/metadata change types
SUMMARY_CHANGED = "summary_changed"
DESCRIPTION_CHANGED = "description_changed"
SECURITY_CHANGED = "security_changed"
