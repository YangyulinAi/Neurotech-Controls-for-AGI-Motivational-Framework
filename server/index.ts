import express, { type Request, Response, NextFunction } from "express";
import helmet from "helmet";
import rateLimit from "express-rate-limit";
import { registerRoutes } from "./routes";
import { setupVite, serveStatic, log } from "./vite";
import { setupWebSocket } from "./websocket";
import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from 'url';

// ES module __dirname equivalent
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables from .env file
dotenv.config();

const app = express();

// Security middleware
app.use(helmet({
  contentSecurityPolicy: false, // Allow Vite's inline scripts in development
  crossOriginEmbedderPolicy: false // Allow WebSocket connections
}));

// Configure trust proxy for rate limiting in production
app.set('trust proxy', 1);

// Enhanced rate limiting with better configuration
app.use(rateLimit({
  windowMs: 60 * 1000, // 1 minute window
  max: 120, // Back to secure 120 requests per minute
  message: {
    error: "Too many requests from this IP",
    message: "Please try again later",
    retryAfter: 60
  },
  standardHeaders: true,
  legacyHeaders: false,
  trustProxy: true,
  // Skip rate limiting for broadcast and WebSocket endpoints during analysis
  skip: (req) => {
    const skipPaths = ['/api/bci/broadcast', '/ws'];
    return skipPaths.some(path => req.path.startsWith(path));
  },
  // Remove deprecated onLimitReached - use handler instead
  handler: (req, res) => {
    console.warn(`Rate limit exceeded for IP: ${req.ip}, path: ${req.path}`);
    res.status(429).json({
      error: "Too many requests from this IP",
      message: "Please try again later",
      retryAfter: 60
    });
  }
}));

// Body parsing with size limits
app.use(express.json({ limit: "1mb" })); // Prevent oversized broadcast messages
app.use(express.urlencoded({ extended: false, limit: "1mb" }));

// Sample download endpoint - expose training samples for download
app.use("/samples", express.static(path.join(__dirname, "../samples")));

app.use((req, res, next) => {
  const start = Date.now();
  const path = req.path;
  let capturedJsonResponse: Record<string, any> | undefined = undefined;

  const originalResJson = res.json;
  res.json = function (bodyJson, ...args) {
    capturedJsonResponse = bodyJson;
    return originalResJson.apply(res, [bodyJson, ...args]);
  };

  res.on("finish", () => {
    const duration = Date.now() - start;
    if (path.startsWith("/api")) {
      let logLine = `${req.method} ${path} ${res.statusCode} in ${duration}ms`;
      if (capturedJsonResponse) {
        logLine += ` :: ${JSON.stringify(capturedJsonResponse)}`;
      }

      if (logLine.length > 80) {
        logLine = logLine.slice(0, 79) + "…";
      }

      log(logLine);
    }
  });

  next();
});

(async () => {
  const server = await registerRoutes(app);
  
  // WebSocket is set up in registerRoutes to avoid duplicate setup

  app.use((err: any, _req: Request, res: Response, _next: NextFunction) => {
    const status = err.status || err.statusCode || 500;
    const message = err.message || "Internal Server Error";

    res.status(status).json({ message });
    throw err;
  });

  // importantly only setup vite in development and after
  // setting up all the other routes so the catch-all route
  // doesn't interfere with the other routes
  if (app.get("env") === "development") {
    await setupVite(app, server);
  } else {
    serveStatic(app);
  }

  // Use port 5000 for development
  const port = process.env.PORT ? parseInt(process.env.PORT) : 5000;
  const host = process.env.HOST || '0.0.0.0'; // Bind to all interfaces for external access
  
  server.listen({
    port,
    host
  }, () => {
    log(`serving on ${host}:${port}`);
  });
})();
