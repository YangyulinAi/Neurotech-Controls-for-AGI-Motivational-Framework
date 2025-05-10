using System;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using UnityEngine;
using System.Collections.Concurrent;

[Serializable]
public class VAData
{
    public double ts;
    public float valence;
    public float arousal;
    public string version;
}

public class BciClientWebSocket : MonoBehaviour
{
    private ClientWebSocket _ws;
    private CancellationTokenSource _cts = new CancellationTokenSource();
    private ConcurrentQueue<VAData> _queue = new ConcurrentQueue<VAData>();

    public float Valence { get; private set; }
    public float Arousal { get; private set; }

    async void Start()
    {
        _ws = new ClientWebSocket();
        var uri = new Uri("ws://localhost:8765");

        try
        {
            await _ws.ConnectAsync(uri, _cts.Token);
            Debug.Log("✅ ClientWebSocket connected");
            _ = ReceiveLoop();  // fire‐and‐forget 接收循环
        }
        catch (Exception ex)
        {
            Debug.LogError("❌ ConnectAsync failed: " + ex);
        }
    }

    private async Task ReceiveLoop()
    {
        var buffer = new byte[1024];
        while (_ws.State == WebSocketState.Open && !_cts.Token.IsCancellationRequested)
        {
            try
            {
                var result = await _ws.ReceiveAsync(new ArraySegment<byte>(buffer), _cts.Token);
                if (result.MessageType == WebSocketMessageType.Close)
                {
                    await _ws.CloseAsync(WebSocketCloseStatus.NormalClosure, "", CancellationToken.None);
                    Debug.Log("🔌 WebSocket closed by server");
                }
                else if (result.MessageType == WebSocketMessageType.Text)
                {
                    var msg = Encoding.UTF8.GetString(buffer, 0, result.Count);
                    // 反序列化并入队
                    var data = JsonUtility.FromJson<VAData>(msg);
                    _queue.Enqueue(data);
                }
            }
            catch (Exception ex)
            {
                Debug.LogError("❌ ReceiveLoop exception: " + ex);
                break;
            }
        }
    }

    void Update()
    {
        while (_queue.TryDequeue(out var data))
        {
            Valence = data.valence;
            Arousal = data.arousal;
            Debug.Log($"[BCI] Valence={Valence:F3}, Arousal={Arousal:F3}");
        }
    }

    void OnDestroy()
    {
        _cts.Cancel();
        _ws?.Dispose();
    }
}
