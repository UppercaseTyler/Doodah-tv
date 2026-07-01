Configuration Field Order

## Decision

Channel configuration fields shall appear in the following order:

1. name
2. number
3. enabled
4. source
5. url

## Rationale

The fields are ordered from user-facing identity to implementation details. This improves readability and keeps configuration files consistent across installations.