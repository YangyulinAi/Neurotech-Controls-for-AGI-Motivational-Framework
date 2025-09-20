# X.on Real-time EEG Connection Setup Guide

> 🏠 **Back to Hub**: [INDEX.md](INDEX.md) | 🔧 **Hardware Guide**: [HARDWARE_GUIDE.md](HARDWARE_GUIDE.md)

This guide helps you set up real-time LSL connection between your local X.on device and the cloud server.

## X.on Device Overview

### Device Specifications
- **Channels**: 8 EEG channels (F3, F4, P3, P4, T7, T8, O1, O2)
- **Sampling Rate**: 500 Hz (automatically resampled to 256 Hz)
- **Reference**: A1, A2 (ear references)
- **FAA Channels**: F3 (left), F4 (right) for frontal alpha asymmetry
- **Connection**: LSL (Lab Streaming Layer) compatible

### Supported Features
- ✅ Dynamic channel detection (no hardcoded channels)
- ✅ Automatic resampling from 500Hz to 256Hz
- ✅ Cross-network LSL configuration
- ✅ Auto-reconnection and error handling
- ✅ Real-time emotion recognition

## Step 1: LSL Configuration Files

### Local Computer (with X.on device)
Copy the configuration from `configs/lsl_api_local.cfg` to `~/lsl_api/lsl_api.cfg`:

```ini
[ports]
MulticastPort = 3051
BasePort      = 3052
PortRange     = 16     ; => 3052–3067

[lab]
KnownPeers = {<SERVER_PUBLIC_IP>}
SessionID  = xon-bridge
```

Replace `<SERVER_PUBLIC_IP>` with your cloud server's public IP address.

### Server
Copy the configuration from `configs/lsl_api_server.cfg` to `~/lsl_api/lsl_api.cfg`:

```ini
[ports]
MulticastPort = 3051
BasePort      = 3052
PortRange     = 16

[lab]
KnownPeers = {<YOUR_HOME_PUBLIC_IP>}
SessionID  = xon-bridge
```

Replace `<YOUR_HOME_PUBLIC_IP>` with your home's public IP address.

## Step 2: Network Configuration

### Home Router Port Forwarding
Configure your home router to forward these ports to your local computer:
- UDP 3051 (LSL discovery)
- TCP/UDP 3052-3067 (LSL data streams)

### Cloud Server Firewall
Configure your cloud server firewall to allow LSL connections:
```bash
# Allow LSL ports
sudo ufw allow 3051/udp
sudo ufw allow 3052:3067/tcp
sudo ufw allow 3052:3067/udp
```

## Step 3: Test Connection

### Start X.on LSL Stream
1. **Connect your X.on device** to your computer via USB
2. **Start X.on software** (X.on Hub or LSL outlet software)
3. **Configure X.on software**:
   - Set sampling rate to 500 Hz
   - Enable LSL streaming
   - Verify all 8 channels are active
4. **Verify stream is running locally**:
   ```python
   from pylsl import resolve_streams
   streams = resolve_streams()
   for stream in streams:
       print(f"Stream: {stream.name()}, Type: {stream.type()}, Channels: {stream.channel_count()}")
   ```

### Start Server Analysis
1. Start the server: `npm run dev` 
2. Start Python analysis: `python scripts/main.py`
3. Watch logs for connection messages

## Step 4: Verify Real-time Data

1. Open the frontend dashboard at your server URL
2. Go to "Real Time Analysis" mode
3. Look for live valence/arousal/phi updates
4. Check WebSocket connection status

## Troubleshooting

### Common Issues

**"No EEG stream found"**
- Verify X.on device is connected and streaming
- Check LSL configuration files are in correct locations
- Verify port forwarding on home router
- Ensure X.on software is running and LSL streaming is enabled

**"Connection timeout"**
- Check firewall rules on both ends
- Verify public IP addresses in config files
- Try VPN connection if behind CGNAT
- Test LSL connection locally first

**"Channel count mismatch"** 
- System auto-detects channels dynamically from LSL stream
- X.on is configured for 8 channels in `configs/device_mapping.json`
- If detection fails, system defaults to 8 channels for X.on
- Verify all 8 channels are active in X.on software

**"Sampling rate issues"**
- X.on runs at 500Hz, system automatically resamples to 256Hz
- Check if resampling is working correctly in logs
- Verify LSL stream reports correct sampling rate

**"Data quality issues"**
- Check electrode impedance in X.on software
- Ensure proper electrode placement (10-20 system)
- Verify reference channels (A1, A2) are connected

### Alternative: VPN Connection
If port forwarding isn't possible (CGNAT), use Tailscale or WireGuard:
1. Install VPN on both local computer and server
2. Use VPN internal IPs in KnownPeers configuration
3. Ports 3051-3067 still need to be accessible within VPN

## Connection Priority

The system searches for EEG streams by type and automatically detects:
1. **Any EEG stream**: The system looks for streams with type "EEG"
2. **Dynamic channel detection**: Automatically detects the number of channels
3. **Device-specific configuration**: Uses X.on configuration from `configs/device_mapping.json`

The system will automatically adapt to your X.on device's specific channel configuration.

## Success Indicators

✅ Server logs: "Connected to LSL stream: [X.on device name]"
✅ Server logs: "Detected N channels from LSL stream"  
✅ Frontend: Live data updates in real-time charts
✅ WebSocket: bci_data messages flowing every few seconds