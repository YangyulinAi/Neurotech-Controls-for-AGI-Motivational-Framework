/**
 * Exponential Moving Average (EMA) smoothing for real-time data
 * Provides beautiful, smooth curves for Φ and other metrics during demos
 */

export class EMASmoothing {
  private alpha: number;
  private lastValue: number | null = null;

  constructor(alpha: number = 0.2) {
    this.alpha = Math.max(0, Math.min(1, alpha)); // Clamp between 0 and 1
  }

  /**
   * Apply EMA smoothing to a single value
   */
  smooth(newValue: number): number {
    if (this.lastValue === null) {
      this.lastValue = newValue;
      return newValue;
    }

    // EMA formula: S(t) = α * X(t) + (1 - α) * S(t-1)
    const smoothed = this.alpha * newValue + (1 - this.alpha) * this.lastValue;
    this.lastValue = smoothed;
    return smoothed;
  }

  /**
   * Reset the smoother
   */
  reset(): void {
    this.lastValue = null;
  }

  /**
   * Get current smoothed value without updating
   */
  getCurrentValue(): number | null {
    return this.lastValue;
  }
}

/**
 * Data throttling for chart updates to prevent browser frame drops
 */
export class DataThrottler {
  private buffer: any[] = [];
  private lastFlush: number = 0;
  private flushInterval: number;

  constructor(intervalMs: number = 100) {
    this.flushInterval = intervalMs;
  }

  /**
   * Add data point to buffer
   */
  add(data: any): boolean {
    this.buffer.push(data);
    
    const now = Date.now();
    if (now - this.lastFlush >= this.flushInterval) {
      this.lastFlush = now;
      return true; // Signal to flush
    }
    
    return false; // Wait for more data
  }

  /**
   * Get buffered data and clear buffer
   */
  flush(): any[] {
    const data = [...this.buffer];
    this.buffer = [];
    return data;
  }

  /**
   * Check if buffer should be flushed
   */
  shouldFlush(): boolean {
    return Date.now() - this.lastFlush >= this.flushInterval;
  }
}

/**
 * Combined smoothing and throttling for optimal chart performance
 */
export class SmoothedThrottler {
  private valenceEMA: EMASmoothing;
  private arousalEMA: EMASmoothing;
  private phiEMA: EMASmoothing;
  private throttler: DataThrottler;

  constructor(alpha: number = 0.2, throttleMs: number = 100) {
    this.valenceEMA = new EMASmoothing(alpha);
    this.arousalEMA = new EMASmoothing(alpha);
    this.phiEMA = new EMASmoothing(alpha);
    this.throttler = new DataThrottler(throttleMs);
  }

  /**
   * Process incoming BCI data with smoothing and throttling
   */
  process(data: { valence: number; arousal: number; phi?: number; timestamp: number }): any[] | null {
    // Apply EMA smoothing
    const smoothedData = {
      valence: this.valenceEMA.smooth(data.valence),
      arousal: this.arousalEMA.smooth(data.arousal),
      phi: data.phi !== undefined ? this.phiEMA.smooth(data.phi) : undefined,
      timestamp: data.timestamp,
      raw_valence: data.valence,
      raw_arousal: data.arousal,
      raw_phi: data.phi
    };

    // Add to throttle buffer
    const shouldFlush = this.throttler.add(smoothedData);
    
    if (shouldFlush) {
      return this.throttler.flush();
    }
    
    return null;
  }

  /**
   * Force flush any remaining buffered data
   */
  forceFlush(): any[] {
    return this.throttler.flush();
  }

  /**
   * Reset all smoothing and throttling state
   */
  reset(): void {
    this.valenceEMA.reset();
    this.arousalEMA.reset();
    this.phiEMA.reset();
    this.throttler.flush(); // Clear buffer
  }
}