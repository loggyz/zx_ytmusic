import { createRequire } from 'module';
const require = createRequire(import.meta.url);

import { SessionManager } from "./session_manager.ts";
import { strerror, VERSION } from "./utils.ts";
import express from "express";

const commander = require("commander");
const { Command } = commander;

const program = new Command().option("-p, --port <PORT>").parse();
// ... baaki ka code ekdam same rehne do


const program = new Command().option("-p, --port <PORT>").parse();

const options = program.opts();

const PORT_NUMBER = options.port || 4416;

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
).on("error", (err: any) => {
    console.error(
        `Could not listen on 0.0.0.0:${PORT_NUMBER} (Caused by ${strerror(err)})`,
    );
});

const sessionManager = new SessionManager();
httpServer.get("/", async (request, response) => {
    response
        .status(400)
        .send(
            "This server is not meant to be accessed directly unless you know what you're doing. Follow the README for plugin/provider setup, and yt-dlp will automatically use the provider: https://github.com/Brainicism/bgutil-ytdlp-pot-provider#readme",
        );
});

httpServer.post("/get_pot", async (request, response) => {
    const body = request.body || {};
    if (body.data_sync_id)
        return response.status(400).send({
            error: "data_sync_id is deprecated, use content_binding instead",
        });
    if (body.visitor_data)
        return response.status(400).send({
            error: "visitor_data is deprecated, use content_binding instead",
        });
    if (body.disable_innertube)
        return response.status(400).send({
            error: "disable_innertube is deprecated because the /Create endpoint doesn't work anymore",
        });

    const contentBinding: string | undefined = body.content_binding;
    const proxy: string = body.proxy;
    const bypassCache: boolean = body.bypass_cache || false;
    const sourceAddress: string | undefined = body.source_address;
    const disableTlsVerification: boolean =
        body.disable_tls_verification || false;

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
        const msg = strerror(e, /*update=*/ true);
        console.error(e.stack);
        response.status(500).send({ error: msg });
    }
});

httpServer.post("/invalidate_caches", async (request, response) => {
    sessionManager.invalidateCaches();
    response.status(204).send();
});

httpServer.post("/invalidate_it", async (request, response) => {
    sessionManager.invalidateIT();
    response.status(204).send();
});

httpServer.get("/ping", async (request, response) => {
    response.send({
        server_uptime: process.uptime(),
        version: VERSION,
    });
});

httpServer.get("/minter_cache", async (request, response) => {
    console.debug(sessionManager.minterCache);
    response.send(Array.from(sessionManager.minterCache.keys()));
});
