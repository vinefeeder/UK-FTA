
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
                    const dfnm = /\\x72\\x65\\x74\\x75\\x72\\x6e\\x20\\x74\\x79\\x70\\x65\\x6f\\x66\\x20([a-z0-9]+)\\[(\\d+)\\]\\.([a-z0-9]+)\\x20\\x3d\\x3d\\x3d\\x20\\x27\\x66\\x75\\x6e\\x63\\x74\\x69\\x6f\\x6e\\x27/gi.exec(b);
                    const krm = /\\x27\\\\x68\\x27:[a-z0-9]+\\.[a-z0-9]+\\((\\d+)\\),'\\\\x61':[a-z0-9]+\\.[a-z0-9]+\\((\\d+)\\)/gi.exec(b);
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
