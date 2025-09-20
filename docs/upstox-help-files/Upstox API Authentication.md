Perform Authentication
The login window is a web page hosted at the following link.
https://api.upstox.com/v2/login/authorization/dialog

Your client application must trigger the opening of the above URL using Webview (or similar technology) and pass the following parameters:
Parameter	Description
client_id	The API key obtained during the app generation process.
redirect_uri	The URL to which the user will be redirected post authentication; must match the URL provided during app generation.
state	An optional parameter. If specified, will be returned after authentication, allowing for state continuity between request and callback.
response_type	This value must always be code.
URL construction:
https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id=<Your-API-Key-Here>&redirect_uri=<Your-Redirect-URI-Here>&state=<Your-Optional-State-Parameter-Here>
Sample URL:
https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id=615b1297-d443-3b39-ba19-1927fbcdddc7&redirect_uri=https%3A%2F%2Fwww.trading.tech%2Flogin%2Fupstox-v2&state=RnJpIERlYyAxNiAyMDIyIDE1OjU4OjUxIEdNVCswNTMwIChJbmRpYSBTdGFuZGFyZCBUaW1lKQ%3D%3D
