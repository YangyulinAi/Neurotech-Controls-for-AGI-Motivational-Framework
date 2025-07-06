import { users, bciData, type User, type InsertUser, type BciData, type InsertBciData } from "@shared/schema";

export interface IStorage {
  getUser(id: number): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  saveBciData(data: InsertBciData): Promise<BciData>;
  getBciDataBySession(sessionId: string): Promise<BciData[]>;
  getRecentBciData(minutes: number): Promise<BciData[]>;
}

export class MemStorage implements IStorage {
  private users: Map<number, User>;
  private bciDataList: BciData[];
  private currentUserId: number;
  private currentBciId: number;

  constructor() {
    this.users = new Map();
    this.bciDataList = [];
    this.currentUserId = 1;
    this.currentBciId = 1;
  }

  async getUser(id: number): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.username === username,
    );
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = this.currentUserId++;
    const user: User = { ...insertUser, id };
    this.users.set(id, user);
    return user;
  }

  async saveBciData(data: InsertBciData): Promise<BciData> {
    const id = this.currentBciId++;
    const bciEntry: BciData = {
      ...data,
      id,
      timestamp: new Date(),
    };
    this.bciDataList.push(bciEntry);
    
    // Keep only last 10000 entries to prevent memory overflow
    if (this.bciDataList.length > 10000) {
      this.bciDataList = this.bciDataList.slice(-10000);
    }
    
    return bciEntry;
  }

  async getBciDataBySession(sessionId: string): Promise<BciData[]> {
    return this.bciDataList.filter(data => data.sessionId === sessionId);
  }

  async getRecentBciData(minutes: number): Promise<BciData[]> {
    const cutoffTime = new Date(Date.now() - minutes * 60 * 1000);
    return this.bciDataList.filter(data => data.timestamp >= cutoffTime);
  }
}

export const storage = new MemStorage();
