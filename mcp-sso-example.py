"""
Example MCP server secured via OAuth 2.1 / OIDC (SSO)

This example uses FastMCP (part of the official MCP Python SDK) and Stytch as an
identity provider to enforce authentication. A similar approach works with
other IdPs like Auth0, Okta or Azure AD. ChatGPT will act as the OAuth
client, redirecting users to the IdP's login page and including the access token
in tool calls.  

To run this example you need:
- An identity provider (IdP) that issues JWT access tokens (e.g. Stytch, Auth0).  
- The FastMCP package installed (`pip install fastmcp`).
- A valid JWKS endpoint, issuer and audience for your IdP.

The code exposes a single tool called `greet` that requires the user to be
authenticated with the `openid` and `profile` scopes.  When ChatGPT calls this
tool, it will include an OAuth access token.  FastMCP verifies the token via
`RemoteAuthProvider` and enforces the declared scopes.

See the accompanying article for details on configuring your IdP and
advertising discovery and PRM endpoints.
"""

from fastmcp import FastMCP, auth
from fastmcp.server.auth import RemoteAuthProvider
from fastmcp.server.auth.providers.jwt import JWTVerifier
from pydantic import AnyHttpUrl

# ----- Identity Provider configuration -----
# Replace the following values with your IdP's JWKS endpoint and token settings.
JWKS_URI = "https://test.stytch.com/v1/sessions/jwks/STYTCH_PROJECT_ID"  # JWKS endpoint for public keys
ISSUER = "https://STYTCH_PROJECT_DOMAIN"  # Expected issuer (iss claim)
AUDIENCE = ["STYTCH_PROJECT_ID"]  # Expected audience (aud claim)

# Create a JWT verifier that will validate incoming access tokens
jwt_verifier = JWTVerifier(
    jwks_uri=JWKS_URI,
    issuer=ISSUER,
    audience=AUDIENCE,
)

# Configure the RemoteAuthProvider.  This automatically advertises
# Protected Resource Metadata (PRM) at /.well-known/oauth-protected-resource and
# sends WWW-Authenticate challenges on 401 responses.  It also validates tokens
# on each tool call.
auth_provider = RemoteAuthProvider(
    token_verifier=jwt_verifier,
    authorization_servers=[AnyHttpUrl("https://STYTCH_PROJECT_DOMAIN")],
    base_url="https://your-mcp-server.example.com",  # publicly accessible URL of this MCP server
)

# Create the FastMCP server with the auth provider
mcp = FastMCP(name="Example SSO API", auth=auth_provider)

# ----- Tool definition -----
# Define a tool that returns a greeting.  It requires OAuth scopes openid and profile.
@mcp.tool(
    name="greet",
    description="Say hello to the current user",
    security_schemes=[auth.OAuth2(scopes=["openid", "profile"])],
)
def greet(name: str) -> str:
    """Return a friendly greeting."""
    return f"Hello, {name}!"


if __name__ == "__main__":
    # Run the MCP server over HTTP.  In production you can enable SSE transport or
    # behind a reverse proxy.  The `transport` argument can be 'http' or 'sse'.
    mcp.run(transport="http", port=8000)
