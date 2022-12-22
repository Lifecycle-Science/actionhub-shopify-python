const AppBridge = window['app-bridge'];
const createApp = AppBridge.default;
const actions = AppBridge.actions;
const Redirect = actions.Redirect;
const Toast = actions.Toast

const authenticatedFetch = window['app-bridge-utils'].authenticatedFetch
const app = createApp(config);


function initApp() {
    getRe2ProgramDetails();
}


/*
PROGRAM DETAILS
 */

function getRe2ProgramDetails() {
    const url = "/program";
    authenticatedFetch(app)(url)
        .then((response) => response.text())
        .then((html) => {
            document.getElementById("divRe2ProgramDetails").innerHTML = html;
            let btn = document.getElementById("btnSubmitProgramChanges")
            document.getElementById("txtHighEngagementThreshold")
                .addEventListener("click", function () {
                    btn.classList.remove("Polaris-Button--disabled")
                });

            document.getElementById("txtEventRelevanceDecay")
                .addEventListener("click", function () {
                    btn.classList.remove("Polaris-Button--disabled")
                });

            document.getElementById("txtActionWeightFloor")
                .addEventListener("click", function () {
                    btn.classList.remove("Polaris-Button--disabled")
                });
            btn.addEventListener("click", function () {
                saveRe2ProgramDetails();
            })
        });
}

function saveRe2ProgramDetails() {
    let btn = document.getElementById("btnSubmitProgramChanges")
    btn.classList.add("Polaris-Button--disabled");

    let highEngagementThreshold = document.getElementById("txtHighEngagementThreshold").value;
    let eventRelevanceDecay = document.getElementById("txtEventRelevanceDecay").value;
    let actionWeightFloor = document.getElementById("txtActionWeightFloor").value;
    const url = "/program";
    authenticatedFetch(app)(url, {
        method:'PUT',
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            "high_engagement_threshold": highEngagementThreshold,
            "event_relevance_decay": eventRelevanceDecay,
            "action_weight_floor": actionWeightFloor
        })})
        .then((response) => response.json())
        .then((data) => {
            console.log(data);
            if ("detail" in data) { showToast(data["detail"], true); }
            else {
                const msg = "Program configuration information changed.";
                showToast(msg, false);;
            }
        });

}


/*
OTHER
 */




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

/*
UTILS
 */

function showToast(message, isError=false) {
    const toastOptions = {
        message: message.toString(),
        duration: 3000,
        isError: isError
    };
    const toastNotice = Toast.create(app, toastOptions);
    console.log("toast", toastOptions);
    toastNotice.dispatch(Toast.Action.SHOW);
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
