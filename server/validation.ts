import { z } from 'zod';
import path from 'path';

// Request validation schemas
// Enhanced validation schemas with balanced security
export const startAnalysisSchema = z.object({
  filename: z.string()
    .min(1, "Filename cannot be empty")
    .max(500, "Filename too long")
    .regex(/^[a-zA-Z0-9._/\s-]+$/, "Invalid filename characters") // Allow spaces, forward slashes and filename chars
    .refine(val => !val.includes(".."), "Path traversal not allowed")
    .refine(val => ['.set', '.fif', '.csv'].some(ext => val.toLowerCase().endsWith(ext)), 
            "Only .set, .fif, and .csv files are supported"),
  computePhi: z.boolean()
    .optional()
    .default(false)
    .transform(val => Boolean(val)), // Ensure boolean type
  phiMethod: z.enum(["mock", "IIT3.0", "IIT4.0_light"])
    .optional()
    .default("mock")
    .transform(val => {
      // Enhanced phiMethod whitelist with detailed logging
      const allowed = new Set(['mock', 'IIT3.0', 'IIT4.0_light']);
      if (!allowed.has(val)) {
        console.warn(`Invalid phiMethod attempted: ${val}, falling back to 'mock'`);
        return 'mock';
      }
      return val;
    }),
  mode: z.enum(["offline", "live"])
    .optional()
    .default("offline")
    .transform(val => val === "live" ? "live" : "offline") // Ensure valid mode
});

export const trainModelSchema = z.object({
  dataFiles: z.array(z.string()).min(1).max(50),
  epochs: z.number().min(1).max(1000).optional().default(50),
  datasetType: z.string().optional().default("emotion"),
  batchSize: z.number().min(1).max(256).optional().default(16),
  learningRate: z.number().min(0.0001).max(0.1).optional().default(0.001),
  windowSize: z.number().min(0.5).max(10).optional().default(1.25),
  overlap: z.number().min(0).max(0.9).optional().default(0),
  computePhi: z.boolean().optional().default(false),
  phiMethod: z.enum(["mock", "IIT3.0", "IIT4.0_light"]).optional().default("mock"),
  phiMaxChannels: z.number().min(1).max(64).optional().default(8)
});

export const testPhiSchema = z.object({
  method: z.enum(["mock", "IIT3.0", "IIT4.0_light"]).optional().default("mock"),
  maxChannels: z.number().min(1).max(64).optional().default(8),
  testSamples: z.number().min(1).max(100).optional().default(4)
});

// File security utilities - updated to match current multi-format support
export const allowedFileExtensions = new Set([".set", ".fif", ".csv"]);

export function validateFileName(filename: string): boolean {
  const ext = path.extname(filename).toLowerCase();
  return allowedFileExtensions.has(ext) && 
         !filename.includes("..") && 
         !filename.includes("/") &&
         filename.length > 0 &&
         filename.length < 255;
}

export function safeJoin(base: string, target: string): string {
  const resolved = path.resolve(path.join(base, target));
  const basePath = path.resolve(base);
  
  if (!resolved.startsWith(basePath + path.sep) && resolved !== basePath) {
    throw new Error("Path traversal attempt detected");
  }
  
  return resolved;
}

// Middleware for request validation
export function validateRequest(schema: z.ZodSchema) {
  return (req: any, res: any, next: any) => {
    const result = schema.safeParse(req.body);
    
    if (!result.success) {
      return res.status(400).json({
        error: "Invalid request body",
        issues: result.error.issues,
        message: "Please check your request parameters"
      });
    }
    
    req.validated = result.data;
    next();
  };
}