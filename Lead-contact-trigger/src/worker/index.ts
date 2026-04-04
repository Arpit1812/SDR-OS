import "dotenv/config";

import { Agenda } from "agenda";
import express from "express";

import { runSendEmailCampaign, CampaignPayload } from "../trigger/emailCampaign.js";
import { runScheduledReplyCheck } from "../trigger/replyChecker.js";

import type { Job } from "agenda";

function requireEnv(name: string): string {
    const value = process.env[name];
    if (!value) {
        throw new Error(`Missing required environment variable: ${name}`);
    }
    return value;
}

function withDbName(mongoUri: string, dbName?: string): string {
    if (!dbName) return mongoUri;

    // If URI already contains a path like /mydb, keep it.
    // mongodb://host:27017/mydb?x=y
    // mongodb+srv://host/mydb?x=y
    const uri = new URL(mongoUri);
    if (uri.pathname && uri.pathname !== "/") return mongoUri;

    uri.pathname = `/${dbName}`;
    return uri.toString();
}

function isAuthOk(req: express.Request): boolean {
    const secret = process.env.WORKER_SECRET;
    if (!secret) return true;

    const auth = req.header("authorization") || "";
    const expected = `Bearer ${secret}`;
    return auth === expected;
}

async function main() {
    const mongoUri = requireEnv("MONGO_URI");

    const mongoDbName = process.env.MONGO_DB_NAME;
    const agenda = new Agenda({
        db: {
            address: withDbName(mongoUri, mongoDbName),
            collection: process.env.AGENDA_COLLECTION || "agendaJobs",
        },
    });

    agenda.define("send-email-campaign", async (job: Job) => {
        const payload = job.attrs.data as CampaignPayload;
        await runSendEmailCampaign(payload);
    });

    agenda.define("scheduled-reply-checker", async () => {
        await runScheduledReplyCheck();
    });

    await agenda.start();

    if ((process.env.ENABLE_REPLY_CHECKER || "").toLowerCase() === "true") {
        const every = process.env.REPLY_CHECK_EVERY || "1 minute";
        await agenda.every(every, "scheduled-reply-checker");
        console.log(`✅ Reply checker scheduled: ${every}`);
    } else {
        console.log("ℹ️ Reply checker disabled (set ENABLE_REPLY_CHECKER=true to enable)");
    }

    const app = express();
    app.use(express.json({ limit: "2mb" }));

    app.get("/health", (_req, res) => {
        res.json({ ok: true });
    });

    app.post("/jobs/send-email-campaign", async (req, res) => {
        if (!isAuthOk(req)) {
            return res.status(401).json({ error: "Unauthorized" });
        }

        const payload: CampaignPayload = (req.body?.payload ?? req.body) as CampaignPayload;

        if (!payload?.campaignId || !payload?.userId || !payload?.backendUrl) {
            return res.status(400).json({ error: "Invalid payload" });
        }

        const job = await agenda.now("send-email-campaign", payload);
        return res.json({
            id: String(job.attrs._id),
            name: job.attrs.name,
            nextRunAt: job.attrs.nextRunAt,
        });
    });

    app.post("/jobs/run-reply-checker", async (req, res) => {
        if (!isAuthOk(req)) {
            return res.status(401).json({ error: "Unauthorized" });
        }

        const job = await agenda.now("scheduled-reply-checker", {});
        return res.json({ id: String(job.attrs._id), name: job.attrs.name });
    });

    const port = parseInt(process.env.PORT || "8787", 10);
    app.listen(port, () => {
        console.log(`✅ Worker listening on http://localhost:${port}`);
    });
}

main().catch((err) => {
    console.error("Worker failed to start:", err);
    process.exit(1);
});
