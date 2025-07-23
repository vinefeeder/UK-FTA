'''
A_n_g_e_l_a 2024
This script is used to extract the AES_KEY and HMAC_SECRET from generated JavaScript code.
It is a fallback method for if and when the API no longer works.
It uses a web browser simulation environment (jsdom) to execute the JavaScript code and retrieve the required values.
The extracted values are then printed to the console.
Note:  Since the routine uses JavaScript, Node needs to be installed on your machine, so as to allow javascript \
to run be run from the command line.
Additionally, use the node packagemanager, nmp, to install jsdom and node-fetch.
'''


import subprocess
import json
import os

js_code = """
const { JSDOM } = require("jsdom");
const fs = require("fs");

async function simulateBrowser() {
    const fetch = await import('node-fetch').then(mod => mod.default);

    const dom = new JSDOM(`<!DOCTYPE html><body></body>`, {
        url: "https://player.akamaized.net/",
        resources: "usable",
        runScripts: "dangerously"
    });
    const window = dom.window;

    window.fetch = fetch;

    try {
        const response = await window.fetch("https://player.akamaized.net/html5player/core/html5-c5-player.js");
        const jsCode = await response.text();
        const scriptElement = window.document.createElement("script");
        scriptElement.textContent = jsCode;
        window.document.body.appendChild(scriptElement);

        const inlineScript = `
            fetch('https://player.akamaized.net/html5player/core/html5-c5-player.js')
                .then((r) => r.text())
                .then((b) => {
                    const dfnm = /\\\\x72\\\\x65\\\\x74\\\\x75\\\\x72\\\\x6e\\\\x20\\\\x74\\\\x79\\\\x70\\\\x65\\\\x6f\\\\x66\\\\x20([a-z0-9]+)\\\\[(\\\\d+)\\\\]\\\\.([a-z0-9]+)\\\\x20\\\\x3d\\\\x3d\\\\x3d\\\\x20\\\\x27\\\\x66\\\\x75\\\\x6e\\\\x63\\\\x74\\\\x69\\\\x6f\\\\x6e\\\\x27/gi.exec(b);
                    const krm = /\\\\x27\\\\\\\\x68\\\\x27:[a-z0-9]+\\\\.[a-z0-9]+\\\\((\\\\d+)\\\\),'\\\\\\\\x61':[a-z0-9]+\\\\.[a-z0-9]+\\\\((\\\\d+)\\\\)/gi.exec(b);
                    if (!dfnm || !krm) {
                        window.simulationResult = { error: 'Regex did not match any content', dfnm, krm };
                        return;
                    }
                    window.simulationResult = {
                        HMAC_SECRET: window[dfnm[1]][dfnm[2]][dfnm[3]](krm[1]),
                        AES_KEY: window[dfnm[1]][dfnm[2]][dfnm[3]](krm[2]),
                    };
                })
                .catch((err) => {
                    window.simulationResult = { error: err.message };
                });
        `;
        const inlineScriptElement = window.document.createElement("script");
        inlineScriptElement.textContent = inlineScript;
        window.document.body.appendChild(inlineScriptElement);

        // Wait for the fetch and processing to complete
        await new Promise(resolve => setTimeout(resolve, 3000));

        // Write the result to a file
        if (window.simulationResult) {
            fs.writeFileSync("output.json", JSON.stringify(window.simulationResult));
        } else {
            fs.writeFileSync("output.json", JSON.stringify({ error: 'Unknown error' }));
        }
    } catch (err) {
        console.error('Error in simulateBrowser:', err);
        fs.writeFileSync("output.json", JSON.stringify({ error: err.message }));
    }
}

simulateBrowser().catch((err) => {
    console.error('Error in simulateBrowser:', err);
    fs.writeFileSync("my5.json", JSON.stringify({ error: err.message }));
});
"""

with open("simulate_browser.js", "w") as f:
    f.write(js_code)
try:
    result = subprocess.run(["node", "simulate_browser.js"], capture_output=True, text=True)
except FileNotFoundError:
    print("Node.js not found. Please ensure it is installed and available in your PATH.")
    exit()

if result.returncode != 0:
    print("Error executing JavaScript file")
    print(result.stderr)
    exit()

if not os.path.exists("output.json"):
    print("output.json file was not created")
    print("Node.js output:", result.stdout)
    exit()

with open("output.json", "r") as f:
    output = json.load(f)

if "error" in output:
    print("Error in JavaScript execution:", output["error"])
else:
    print(output)
