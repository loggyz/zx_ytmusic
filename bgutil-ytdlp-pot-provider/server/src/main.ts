import { SessionManager } from "./session_manager.ts";
import { strerror, VERSION } from "./utils.ts";
import express from "express";

// Commander hata diya, seedha port set kar rahe hain
const PORT_NUMBER = 4416;

const httpServer = express();
httpServer.use(express.json());
httpServer.use(express.urlencoded({ extended: true }));

httpServer.listen(
    {
        host: "0.0.0.0",
        port: PORT_NUMBER,
    },
    () => {
        console.log(
            `Started POT server (v${VERSION}) on address 0.0.0.0:${PORT_NUMBER}`,
        );
    }
);

const sessionManager = new SessionManager();

httpServer.get("/", async (request, response) => {
    response
        .status(400)
        .send("POT Server is Active.");
});

httpServer.post("/get_pot", async (request, response) => {
    const body = request.body || {};
    const contentBinding: string | undefined = body.content_binding;
    const proxy: string = body.proxy;
    const bypassCache: boolean = body.bypass_cache || false;
    const sourceAddress: string | undefined = body.source_address;
    const disableTlsVerification: boolean = body.disable_tls_verification || false;

    try {
        const sessionData = await sessionManager.generatePoToken(
            contentBinding,
            proxy,
            bypassCache,
            sourceAddress,
            disableTlsVerification,
            body.challenge,
            body.innertube_context,
        );
        response.send(sessionData);
    } catch (e) {
        const msg = strerror(e, true);
        console.error(e.stack);
        response.status(500).send({ error: msg });
    }
});

httpServer.get("/ping", async (request, response) => {
    response.send({
        server_uptime: process.uptime(),
        version: VERSION,
    });
});
