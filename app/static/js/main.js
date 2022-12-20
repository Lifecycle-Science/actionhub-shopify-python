const AppBridge = window['app-bridge'];
const createApp = AppBridge.default;
const actions = AppBridge.actions;
const Redirect = actions.Redirect;

const authenticatedFetch = window['app-bridge-utils'].authenticatedFetch
const app = createApp(config);


function getRe2ProgramDetails() {
    const url = "/re2/program";
    authenticatedFetch(app)(url)
        .then((response) => response.text())
        .then((html) => {
            console.log(html)
            document.getElementById("divRe2ProgramDetails").innerHTML = html;
        });
    }


function initApp() {
    getRe2ProgramDetails();
}


function callHome() {
  const url = "/test_client";
  authenticatedFetch(app)(url)
      .then((response) => response.json())
      .then((data) => {
        console.log(data);
        if ("request_scope_resource" in data) {
            authRedirect(data["request_scope_resource"])
        }
      });
}

function authRedirect(request_scope_resource) {
    const params = new URLSearchParams(window.location.search);
    params.delete('embedded');
    let redirectUri = "";
    redirectUri = "https://" + location.hostname
    redirectUri += request_scope_resource
    redirectUri += "?" + params.toString()

    console.log("redirect...")
    alert(redirectUri)

    const redirect = Redirect.create(app);
    redirect.dispatch(
        Redirect.Action.REMOTE,
        decodeURIComponent(redirectUri)
    );
}
