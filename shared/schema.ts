import { pgTable, text, serial, integer, boolean, timestamp, real } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

export const bciData = pgTable("bci_data", {
  id: serial("id").primaryKey(),
  valence: real("valence").notNull(),
  arousal: real("arousal").notNull(),
  timestamp: timestamp("timestamp").notNull().defaultNow(),
  sessionId: text("session_id"),
});

export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});

export const insertBciDataSchema = createInsertSchema(bciData).pick({
  valence: true,
  arousal: true,
  sessionId: true,
});

export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;
export type BciData = typeof bciData.$inferSelect;
export type InsertBciData = z.infer<typeof insertBciDataSchema>;
