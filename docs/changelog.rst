Changelog
=========

Release 1.3.0 (October 7, 2024)
-------------------------------

Features:
 * OAuth 2.0 Rich Authorization Requests (`RFC 9396 <https://datatracker.ietf.org/doc/html/rfc9396>`_)


Release 1.2.0 (August 7, 2024)
------------------------------

Features:
 * Grant Types: Client Credentials and Password.
 * Tokens will refresh if the response from the server includes a Expires in field.
 * Refresh tokens will be used if included in the response from the server.


Release 1.1.0 (May 14, 2024)
----------------------------

In the CRUDs package, Interfaces can now be generated through YAML Configuration
files. This is for API's that have many models with common request types.
