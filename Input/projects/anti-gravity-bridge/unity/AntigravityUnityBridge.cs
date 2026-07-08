#if UNITY_EDITOR || UNITY_STANDALONE
using System;
using System.Collections.Concurrent;
using System.Text;
using UnityEngine;
using UnityEditor;
using UnityEngine.Networking;

// Note: To compile the WebSocket receiver block, ensure the 'NativeWebSocket' package is installed.
// URL: https://github.com/endel/NativeWebSocket
#if HAVE_NATIVE_WEBSOCKET
using NativeWebSocket;
#endif

namespace Antigravity.Unity
{
    /// <summary>
    /// Editor window connecting Unity to the Anti-Gravity Bridge Orchestrator.
    /// Updated for the v2 BridgeCommand API contracts.
    /// </summary>
    public class AntigravityUnityBridge : EditorWindow
    {
        private string orchestratorUrl = "http://localhost:8420";
        private string lastStatus = "Disconnected";
        private string commandAction = "sync_assets";
        private string commandPayload = "{\"project\": \"island_game\"}";

        [MenuItem("Tools/Antigravity/Open Bridge")]
        public static void ShowWindow()
        {
            GetWindow<AntigravityUnityBridge>("Antigravity Bridge");
        }

        private void OnGUI()
        {
            GUILayout.Label("Anti-Gravity Bridge Connection (v2)", EditorStyles.boldLabel);
            orchestratorUrl = EditorGUILayout.TextField("Orchestrator URL", orchestratorUrl);

            EditorGUILayout.Space();

            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Check Health"))
            {
                CheckHealth();
            }
            GUILayout.EndHorizontal();

            EditorGUILayout.LabelField("Bridge Status:", lastStatus, EditorStyles.helpBox);

            EditorGUILayout.Space();
            GUILayout.Label("Send Custom v1 Command", EditorStyles.boldLabel);
            commandAction = EditorGUILayout.TextField("Command Type", commandAction);
            GUILayout.Label("Payload (JSON String):");
            commandPayload = EditorGUILayout.TextArea(commandPayload, GUILayout.Height(60));

            if (GUILayout.Button("Dispatch Command (v2 Accepted)"))
            {
                SendCommand(commandAction, commandPayload);
            }
        }

        private async void CheckHealth()
        {
            lastStatus = "Checking health...";
            string url = $"{orchestratorUrl.TrimEnd('/')}/health";

            using (UnityWebRequest webRequest = UnityWebRequest.Get(url))
            {
                var operation = webRequest.SendWebRequest();
                while (!operation.isDone)
                {
                    System.Threading.Tasks.Task.Delay(50).GetAwaiter().GetResult();
                }

                if (webRequest.result == UnityWebRequest.Result.Success)
                {
                    lastStatus = $"Operational: {webRequest.downloadHandler.text}";
                    Debug.Log($"[AntiGravity Bridge] Health: {webRequest.downloadHandler.text}");
                }
                else
                {
                    lastStatus = $"Error: {webRequest.error}";
                    Debug.LogError($"[AntiGravity Bridge] Health check failed: {webRequest.error}");
                }
            }
        }

        private void SendCommand(string commandType, string payloadJson)
        {
            lastStatus = "Sending command...";
            string url = $"{orchestratorUrl.TrimEnd('/')}/api/bridge/command";

            // Generate payload conforming to v2 BridgeCommand schema
            string jsonBody = "{\n" +
                $"  \"schema_version\": \"bridge.command.v1\",\n" +
                $"  \"command_id\": \"cmd_{System.Guid.NewGuid().ToString().Replace(\"-\", \"\").Substring(0, 12)}\",\n" +
                $"  \"command_type\": \"unity.{commandType}\",\n" +
                "  \"target\": \"unity\",\n" +
                "  \"dry_run\": false,\n" +
                "  \"priority\": 50,\n" +
                $"  \"payload\": {payloadJson}\n" +
                "}";

            UnityWebRequest webRequest = new UnityWebRequest(url, "POST");
            byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonBody);
            webRequest.uploadHandler = new UploadHandlerRaw(bodyRaw);
            webRequest.downloadHandler = new DownloadHandlerBuffer();
            webRequest.SetRequestHeader("Content-Type", "application/json");

            var operation = webRequest.SendWebRequest();
            while (!operation.isDone)
            {
                System.Threading.Tasks.Task.Delay(50).GetAwaiter().GetResult();
            }

            if (webRequest.result == UnityWebRequest.Result.Success || webRequest.responseCode == 202)
            {
                lastStatus = $"Accepted: {webRequest.downloadHandler.text}";
                Debug.Log($"[AntiGravity Bridge] Command Accepted: {webRequest.downloadHandler.text}");
            }
            else
            {
                lastStatus = $"Command Failed: {webRequest.error}";
                Debug.LogError($"[AntiGravity Bridge] Command error: {webRequest.error}\nResponse: {webRequest.downloadHandler.text}");
            }
        }
    }

    [Serializable]
    public class BridgeEvent
    {
        public string type;
        public string job_id;
        public string command_type;
    }

    /// <summary>
    /// Runtime MonoBehaviour to connect to the FastAPI WebSocket event bus.
    /// Dispatches inbound completed jobs and sync events on the main Unity thread.
    /// </summary>
    public sealed class AntigravityWebSocketReceiver : MonoBehaviour
    {
#if HAVE_NATIVE_WEBSOCKET
        [SerializeField] private string wsUrl = "ws://127.0.0.1:8420/ws/events";
        private WebSocket _ws;
        private readonly ConcurrentQueue<Action> _mainThreadQueue = new ConcurrentQueue<Action>();

        private async void Start()
        {
            _ws = new WebSocket(wsUrl);

            _ws.OnOpen += () => Debug.Log("[Bridge WebSocket] Connected");
            _ws.OnError += e => Debug.LogError("[Bridge WebSocket] Error: " + e);
            _ws.OnClose += code => Debug.Log("[Bridge WebSocket] Closed: " + code);

            _ws.OnMessage += bytes =>
            {
                var json = Encoding.UTF8.GetString(bytes);
                var evt = JsonUtility.FromJson<BridgeEvent>(json);

                if (evt == null) return;

                _mainThreadQueue.Enqueue(() =>
                {
                    if (evt.type == "job.completed" || evt.command_type == "unity.create_primitive")
                    {
                        var cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
                        cube.name = $"BridgeCube_{DateTime.UtcNow:HHmmss}";
                        cube.transform.position = new Vector3(0, 1, 0);
                        Debug.Log($"[Bridge WebSocket] Spawned GameObject: {cube.name}");
                    }
                });
            };

            await _ws.Connect();
        }

        private async void Update()
        {
            while (_mainThreadQueue.TryDequeue(out var action))
            {
                action.Invoke();
            }

            if (_ws != null && _ws.State == WebSocketState.Open)
            {
                await _ws.SendText("ping");
            }
        }

        private async void OnDestroy()
        {
            if (_ws != null)
            {
                await _ws.Close();
            }
        }
#else
        private void Start()
        {
            Debug.LogWarning("[AntigravityWebSocketReceiver] NativeWebSocket is not active. Import it to enable real-time runtime events.");
        }
#endif
    }
}
#endif
