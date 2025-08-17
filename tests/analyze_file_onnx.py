#!/usr/bin/env python3
"""
Unified EEG file analysis script supporting .set/.fif/.csv formats
Enhanced with automatic format detection, epochs fallback, and CSV sampling rate adaptation
"""
import os, sys, json, time, argparse
import numpy as np
import requests
import mne
import pandas as pd

# Project internal imports - maintain consistency with existing naming
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from preprocess import Preprocessor, extract_feats
from onnx_runner import ONNXRunner

# Enhanced Φ import strategy: prioritize real Φ (PyPhi), fallback to enhanced simulation
try:
    from phi_estimator import PhiEstimator as _PhiEstimator  # Real Φ (PyPhi)
    _HAVE_REAL = True
    print("[PHI] Real PyPhi-based Φ estimator loaded")
except Exception as e:
    from phi_estimator_enhanced import PhiEstimatorEnhanced as _PhiEstimator  # Approximated Φ
    _HAVE_REAL = False
    print(f"[PHI] PyPhi not available ({e}), using enhanced simulation")

def jlog(**kw): 
    """JSON logging for structured output"""
    print(json.dumps(kw, ensure_ascii=False), flush=True)

def epochs_to_raw(epochs: mne.Epochs) -> mne.io.Raw:
    """Convert epochs back to continuous raw data"""
    data = epochs.get_data()  # (n_epochs, n_channels, n_timepoints)
    X = data.transpose(1, 0, 2).reshape(data.shape[1], -1, order="C")
    info = mne.create_info(epochs.ch_names, epochs.info["sfreq"], "eeg")
    return mne.io.RawArray(X, info)

def load_csv_as_raw(csv_path: str, fs_hint: float = 256.0) -> mne.io.Raw:
    """Load CSV with automatic sampling rate detection and NaN/Inf cleaning"""
    df = pd.read_csv(csv_path)
    cols = [str(c).lower() for c in df.columns]
    
    # Check if first column contains time/timestamp information
    has_time = any(k in cols[0] for k in ["time", "timestamp", "sample"])
    
    if has_time:
        t = df.iloc[:, 0].to_numpy(dtype=float)
        X = df.iloc[:, 1:].to_numpy(dtype=float).T  # channels × timepoints
        
        # Estimate sampling rate from time differences
        dt = np.diff(t)
        good = np.isfinite(dt) & (dt > 0)
        fs = float(np.round(1/np.median(dt[good]))) if good.any() else float(fs_hint)
    else:
        X = df.to_numpy(dtype=float).T
        fs = float(fs_hint)
    
    # Clean NaN and infinite values
    X[~np.isfinite(X)] = 0.0
    
    # Create MNE Raw object
    info = mne.create_info([f"CH{i+1}" for i in range(X.shape[0])], fs, "eeg")
    return mne.io.RawArray(X, info)

def load_any(filepath: str, fs_hint: float = 256.0) -> mne.io.Raw:
    """Unified loader for .set/.fif/.csv with automatic format detection"""
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == ".set":
        return mne.io.read_raw_eeglab(filepath, preload=True, verbose=False)
    elif ext == ".fif":
        try:
            # First try as raw data
            return mne.io.read_raw_fif(filepath, preload=True, verbose=False)
        except Exception:
            # Fallback to epochs (like -epo.fif files)
            epochs = mne.read_epochs(filepath, preload=True, verbose=False)
            return epochs_to_raw(epochs)
    elif ext == ".csv":
        return load_csv_as_raw(filepath, fs_hint=fs_hint)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def parse_args():
    """Parse command line arguments with enhanced options"""
    ap = argparse.ArgumentParser(description="Unified EEG analysis with ONNX inference")
    ap.add_argument("filepath", help="Path to EEG file (.set/.fif/.csv)")
    ap.add_argument("--compute_phi", action="store_true", help="Enable Φ (phi) computation")
    ap.add_argument("--phi_method", default="mock", choices=["mock", "IIT3.0", "IIT4.0_light"],
                   help="Φ computation method")
    ap.add_argument("--broadcast_url", default="http://localhost:5000/api/bci/broadcast",
                   help="WebSocket broadcast endpoint")
    ap.add_argument("--fs_hint", type=float, default=256.0,
                   help="Sampling rate hint for CSV files")
    ap.add_argument("--win", type=float, default=1.0,
                   help="Window size in seconds")
    ap.add_argument("--step", type=float, default=0.25,
                   help="Step size in seconds")
    return ap.parse_args()

def main():
    """Main analysis pipeline with enhanced error handling"""
    args = parse_args()
    
    try:
        # Load EEG data with unified loader
        raw = load_any(args.filepath, fs_hint=args.fs_hint)
        fs = int(raw.info["sfreq"])
        data = raw.get_data()  # channels × timepoints
        
        print(f"[INFO] Loaded {args.filepath}: {data.shape[0]} channels, {data.shape[1]} samples at {fs} Hz")
        
        # Initialize processing components
        pre = Preprocessor(fs, 1, 45)  # 1-45 Hz bandpass
        onnx = ONNXRunner("model/va_regressor.onnx", use_gpu=True)
        
        if args.compute_phi:
            # Initialize Φ estimator with unified interface
            phi_est = _PhiEstimator(method=args.phi_method, max_channels=6)  # ≤6 nodes to avoid PyPhi degradation
            info = getattr(phi_est, "get_info", lambda: {"available": _HAVE_REAL})()
            print(f"[PHI] backend_ready={info.get('backend_ready', _HAVE_REAL)}, method={args.phi_method}")
        
        # Window-based analysis
        win = int(fs * args.win)
        step = int(fs * args.step)
        
        results = []
        window_count = 0
        
        for start in range(0, data.shape[1] - win, step):
            seg = data[:, start:start+win]            # channels × window
            seg_t = seg.T                             # window × channels
            
            # Preprocessing (maintain existing interface)
            pre_t = pre.transform(seg_t).T            # channels × window
            
            # Feature extraction (reuse existing interface)
            spec3, de = extract_feats(pre_t.T, fs)    # spec: 3×224×224, de: 26D
            
            # ONNX inference
            prediction = onnx.predict(spec3[np.newaxis, ...], de[np.newaxis, ...])
            if isinstance(prediction, tuple) and len(prediction) == 2:
                val, aro = prediction
            elif hasattr(prediction, '__len__') and len(prediction) >= 2:
                val, aro = prediction[0], prediction[1]
            else:
                # Single output case - assume it's [valence, arousal]
                if hasattr(prediction, '__getitem__'):
                    val, aro = prediction[0], prediction[1] if len(prediction) > 1 else prediction[0]
                else:
                    val = aro = float(prediction)  # Fallback
            
            # Prepare payload
            timestamp = start / fs
            payload = {
                "valence": float(val),
                "arousal": float(aro),
                "timestamp": float(timestamp),
                "type": "bci_data"
            }
            
            # Φ computation with unified interface (real or enhanced simulation)
            if args.compute_phi:
                # Limit to 6 channels (recommended: O1, Oz, O2, PO7, PO8, Pz) for optimal PyPhi performance
                phi_input = pre_t[:6, :] if pre_t.shape[0] >= 6 else pre_t
                
                # Use unified interface - both estimators support estimate_phi
                if hasattr(phi_est, 'estimate_phi'):
                    if _HAVE_REAL:
                        # Real Φ estimator returns float directly
                        phi_value = phi_est.estimate_phi(phi_input)
                    else:
                        # Enhanced estimator returns dict with "phi" key
                        phi_result = phi_est.estimate_phi(phi_input, fs)
                        phi_value = phi_result["phi"] if isinstance(phi_result, dict) else phi_result
                else:
                    # Fallback: use compute method for batch processing
                    import torch
                    phi_tensor = torch.tensor(phi_input, dtype=torch.float32).unsqueeze(0)
                    phi_values = phi_est.compute(phi_tensor)
                    phi_value = float(phi_values[0])
                
                payload["phi"] = float(phi_value)
            
            # Broadcast to WebSocket
            try:
                response = requests.post(args.broadcast_url, json=payload, timeout=1.0)
                if response.status_code == 200:
                    jlog(action="broadcast_success", window=window_count, **payload)
                else:
                    jlog(action="broadcast_failed", status=response.status_code, window=window_count)
            except requests.RequestException as e:
                jlog(action="broadcast_error", error=str(e), window=window_count)
            
            # Console output for monitoring
            phi_str = f", Φ={payload.get('phi', 'N/A'):.3f}" if args.compute_phi else ""
            print(f"[ANALYSIS-OUT] Window {window_count} (t={timestamp:.1f}s): "
                  f"Valence={val:.3f}, Arousal={aro:.3f}{phi_str}")
            
            results.append(payload)
            window_count += 1
        
        # Analysis summary
        avg_valence = np.mean([r["valence"] for r in results])
        avg_arousal = np.mean([r["arousal"] for r in results])
        
        print(f"[ANALYSIS-OUT] Analysis Summary:")
        print(f"==============================")
        print(f"Total Windows Processed: {window_count}")
        print(f"Average Valence: {avg_valence:.3f}")
        print(f"Average Arousal: {avg_arousal:.3f}")
        
        # Save results
        output_path = args.filepath.replace(os.path.splitext(args.filepath)[1], "_onnx_analysis.json")
        with open(output_path, "w") as f:
            json.dump({
                "file": args.filepath,
                "total_windows": window_count,
                "avg_valence": avg_valence,
                "avg_arousal": avg_arousal,
                "results": results,
                "parameters": {
                    "window_size": args.win,
                    "step_size": args.step,
                    "sampling_rate": fs,
                    "compute_phi": args.compute_phi,
                    "phi_method": args.phi_method if args.compute_phi else None
                }
            }, f, indent=2)
        
        jlog(action="analysis_summary", windows_processed=window_count, 
             avg_valence=avg_valence, avg_arousal=avg_arousal, 
             results_saved=output_path)
        
        # Broadcast completion
        completion_payload = {
            "type": "analysis_complete",
            "message": f"Analysis complete: {window_count} windows processed",
            "avg_valence": avg_valence,
            "avg_arousal": avg_arousal,
            "total_windows": window_count
        }
        
        try:
            requests.post(args.broadcast_url, json=completion_payload, timeout=1.0)
            jlog(action="completion_broadcast_sent")
        except:
            pass
        
        print(f"[ANALYSIS-OUT] Detailed results saved to: {output_path}")
        jlog(action="analysis_complete", status="success", windows_processed=window_count)
        
    except Exception as e:
        print(f"[ERROR] Analysis failed: {str(e)}")
        jlog(action="analysis_failed", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()