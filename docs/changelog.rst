Changelog
=========

Release 1.4.0 (June 30, 2025)
------------------------------

Features:
 - Updated supported Python versions for 3.9 to 3.12. Python 3.8 is no longer supported.
 - URLLib3 2.5.0 is now supported, and updated SSL Certificate Verification.
 - OAuth2 state is now transparently encrypted and decrypted to prevent token leakage.
 - OAuth2 now supports the Authorization Code flow with state parameter for CSRF protection.
 - PlanHat auto-chunk support for large datasets

Release 1.3.9 (November 7, 2024)
--------------------------------

Features:
 - Planhat Create Activity bulk mode to upload multiple entries in one request.

Release 1.3.8 (November 5, 2024)
--------------------------------

Features:
 - Planhat Bulk Upsert response is now a single dictionary instead of a list of
   dictionaries.  The values of all response are summaries or extended together.

Fixes:
 - Correct the method used by the Planhat interfaces bulk_insert_metrics.

Release 1.3.6 (November 4, 2024)
--------------------------------

Fixes:
 - Allow Any data type to be serialized and deserialized to JSON.
 - Corrected the Planhat Metric model to correctly use bulk_insert_metrics.
 - Planhat bulk_upsert method required replace argument to be set to True.

Release 1.3.3 (October 21, 2024)
--------------------------------

Fixes:
 - Adjust the setup so Interfaces are included in the package.
 - Update to Authorization in request_headers to stop concatenation.

Release 1.3.1 (October 20, 2024)
--------------------------------

Updates:
 - Renamed the ``Auth`` Abstract Base Class to ``AuthABC``.
 - Made the PoolManager or ProxyManger attribute ``manager`` public.
 - Made the HTTPHeaderDict attribute ``request_headers`` public.
 - Retries applies to all URLLib3 retry types instead of only connect.
 - Added 'Request Timeout' and 'Too Early' default retry status codes.
 - status_whitelist renamed to status_ignore for better representation.

Release 1.3.0 (October 7, 2024)
-------------------------------

Features:
 - OAuth 2.0 Rich Authorization Requests (`RFC 9396 <https://datatracker.ietf.org/doc/html/rfc9396>`_)

Release 1.2.0 (August 7, 2024)
------------------------------

Features:
 - Initial implmentation of OAuth 2.0 Authorization Grant
     - Resource Owner Password Credientals
       (`Section 1.3.3 RFC 6749 <https://www.rfc-editor.org/rfc/rfc6749#section-1.3.3>`_)
     - Client Credentials
       (`Section 1.3.4 RFC 6749 <https://www.rfc-editor.org/rfc/rfc6749#section-1.3.4>`_)
     - Refresh tokens will be used if included in the response from the server.
       (`Section 1.5 RFC 6749 <https://www.rfc-editor.org/rfc/rfc6749#section-1.5>`_)

Release 1.1.0 (May 14, 2024)
----------------------------

In the CRUDs package, Interfaces can now be generated through YAML Configuration
files. This is for APIs that have many models with common request types.
