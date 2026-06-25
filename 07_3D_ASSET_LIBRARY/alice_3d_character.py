"""
ALICE - Interactive 3D Character System for ISLAND
Real-time character interaction, animation, and dialogue system
"""

import json
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime


class AnimationType(Enum):
    """ALICE animation types"""
    IDLE = "idle"
    WALK = "walk"
    RUN = "run"
    JUMP = "jump"
    TALK = "talk"
    GESTURE = "gesture"
    DANCE = "dance"
    SIT = "sit"
    STAND = "stand"
    WAVE = "wave"
    THINK = "think"


@dataclass
class Vector3:
    """3D Vector representation"""
    x: float
    y: float
    z: float

    def to_dict(self):
        return {"x": self.x, "y": self.y, "z": self.z}

    def distance_to(self, other: 'Vector3') -> float:
        return np.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)


@dataclass
class Rotation:
    """Euler rotation in degrees"""
    pitch: float  # X-axis (up/down)
    yaw: float    # Y-axis (left/right)
    roll: float   # Z-axis (tilt)

    def to_dict(self):
        return {"pitch": self.pitch, "yaw": self.yaw, "roll": self.roll}


@dataclass
class CharacterMaterial:
    """Material properties for character rendering"""
    color: str = "#ffffff"
    metalness: float = 0.0
    roughness: float = 0.8
    emissive: str = "#000000"
    opacity: float = 1.0

    def to_dict(self):
        return asdict(self)


@dataclass
class AnimationFrame:
    """Single animation frame"""
    time: float
    position: Vector3
    rotation: Rotation
    scale: Vector3 = field(default_factory=lambda: Vector3(1, 1, 1))


class ALICE3D:
    """ALICE - Advanced Live Interactive Character Engine"""

    def __init__(self, name: str = "ALICE", model_path: str = None, texture_path: str = None):
        self.name = name
        self.model_path = model_path or "07_3D_ASSET_LIBRARY/alice.glb"
        self.texture_path = texture_path or "07_3D_ASSET_LIBRARY/alice_texture.png"
        
        # Core transform properties
        self.position = Vector3(0, 0, 0)
        self.rotation = Rotation(0, 0, 0)
        self.scale = Vector3(1, 1, 1)
        
        # Character state
        self.current_animation = AnimationType.IDLE
        self.animation_speed = 1.0
        self.animation_loop = False
        self.animation_progress = 0.0
        
        # Material and appearance
        self.material = CharacterMaterial(color="#00ff88")
        self.is_visible = True
        self.alpha_value = 1.0
        
        # Movement and physics
        self.is_moving = False
        self.velocity = Vector3(0, 0, 0)
        self.max_speed = 5.0
        self.acceleration = 0.1
        
        # Animation and dialogue
        self.is_talking = False
        self.current_dialogue = ""
        self.dialogue_duration = 0.0
        self.current_gesture = None
        self.gesture_intensity = 0.5
        
        # Animation queues
        self.animation_queue: List[Tuple[AnimationType, float, bool]] = []
        self.dialogue_queue: List[Dict] = []
        self.gesture_queue: List[str] = []
        
        # Keyframe animations
        self.keyframes: Dict[str, List[AnimationFrame]] = {}
        
        # State tracking
        self.state_history: List[Dict] = []
        self.creation_time = datetime.now().isoformat()
        self.last_update_time = datetime.now().isoformat()

    def load_model(self, model_path: str, texture_path: Optional[str] = None):
        """Load 3D model and optional texture"""
        self.model_path = model_path
        if texture_path:
            self.texture_path = texture_path
        return self

    def set_position(self, x: float, y: float, z: float):
        """Set character position in 3D space"""
        self.position = Vector3(x, y, z)
        return self

    def set_rotation(self, pitch: float, yaw: float, roll: float):
        """Set character rotation (Euler angles in degrees)"""
        self.rotation = Rotation(pitch, yaw, roll)
        return self

    def set_scale(self, x: float = 1.0, y: float = 1.0, z: float = 1.0):
        """Set character scale"""
        self.scale = Vector3(x, y, z)
        return self

    def move_to(self, target_x: float, target_y: float, target_z: float, duration: float = 1.0, run: bool = False):
        """Animate character movement to target position"""
        animation = AnimationType.RUN if run else AnimationType.WALK
        self.animation_queue.append((animation, duration, True))
        
        # Linear interpolation path
        steps = int(duration * 30)  # 30 FPS
        for i in range(steps):
            t = i / steps
            x = self.position.x + (target_x - self.position.x) * t
            y = self.position.y + (target_y - self.position.y) * t
            z = self.position.z + (target_z - self.position.z) * t
        
        self.position = Vector3(target_x, target_y, target_z)
        self.is_moving = False
        return self

    def play_animation(self, animation_type: AnimationType, duration: float = 1.0, loop: bool = False):
        """Queue animation to play"""
        self.current_animation = animation_type
        self.animation_queue.append((animation_type, duration, loop))
        return self

    def talk(self, text: str, duration: Optional[float] = None):
        """Make ALICE talk with dialogue"""
        self.is_talking = True
        if duration is None:
            duration = len(text) * 0.05  # Rough estimate: ~50ms per character
        
        self.current_dialogue = text
        self.dialogue_duration = duration
        self.animation_queue.append((AnimationType.TALK, duration, False))
        
        dialogue_entry = {
            "text": text,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        self.dialogue_queue.append(dialogue_entry)
        return dialogue_entry

    def gesture(self, gesture_name: str, intensity: float = 0.5, duration: float = 0.5):
        """Add gesture animation (wave, point, nod, etc.)"""
        self.current_gesture = gesture_name
        self.gesture_intensity = min(1.0, max(0.0, intensity))
        self.gesture_queue.append(gesture_name)
        self.animation_queue.append((AnimationType.GESTURE, duration, False))
        return self

    def look_at(self, target_x: float, target_y: float, target_z: float):
        """Make ALICE look at target position"""
        target = Vector3(target_x, target_y, target_z)
        direction = Vector3(
            target.x - self.position.x,
            target.y - self.position.y,
            target.z - self.position.z
        )
        
        # Calculate rotation angles
        import math
        yaw = math.atan2(direction.x, direction.z) * 180 / math.pi
        distance_xz = math.sqrt(direction.x**2 + direction.z**2)
        pitch = math.atan2(-direction.y, distance_xz) * 180 / math.pi
        
        self.rotation = Rotation(pitch, yaw, 0)
        return self

    def set_material(self, color: str = None, metalness: float = None, roughness: float = None, opacity: float = None):
        """Update character material properties"""
        if color:
            self.material.color = color
        if metalness is not None:
            self.material.metalness = metalness
        if roughness is not None:
            self.material.roughness = roughness
        if opacity is not None:
            self.material.opacity = opacity
        return self

    def add_keyframe_animation(self, name: str, frames: List[AnimationFrame]):
        """Add custom keyframe animation"""
        self.keyframes[name] = frames
        return self

    def dance(self, dance_type: str = "default", duration: float = 3.0):
        """Make ALICE dance"""
        self.animation_queue.append((AnimationType.DANCE, duration, False))
        return self

    def think(self, duration: float = 1.0):
        """Make ALICE appear to be thinking"""
        self.animation_queue.append((AnimationType.THINK, duration, False))
        return self

    def wave(self, duration: float = 0.8):
        """Make ALICE wave"""
        self.gesture(gesture_name="wave", duration=duration)
        return self

    def toggle_visibility(self):
        """Toggle character visibility"""
        self.is_visible = not self.is_visible
        return self

    def get_state(self) -> Dict:
        """Get current character state"""
        return {
            "name": self.name,
            "position": self.position.to_dict(),
            "rotation": self.rotation.to_dict(),
            "scale": self.scale.to_dict(),
            "animation": self.current_animation.value,
            "isMoving": self.is_moving,
            "isTalking": self.is_talking,
            "currentDialogue": self.current_dialogue,
            "currentGesture": self.current_gesture,
            "visible": self.is_visible,
            "material": self.material.to_dict()
        }

    def to_dict(self) -> Dict:
        """Export character as dictionary"""
        return {
            "name": self.name,
            "modelPath": self.model_path,
            "texturePath": self.texture_path,
            "position": self.position.to_dict(),
            "rotation": self.rotation.to_dict(),
            "scale": self.scale.to_dict(),
            "currentAnimation": self.current_animation.value,
            "animationSpeed": self.animation_speed,
            "animationProgress": self.animation_progress,
            "material": self.material.to_dict(),
            "isMoving": self.is_moving,
            "isTalking": self.is_talking,
            "currentDialogue": self.current_dialogue,
            "dialogueDuration": self.dialogue_duration,
            "currentGesture": self.current_gesture,
            "gestureIntensity": self.gesture_intensity,
            "visible": self.is_visible,
            "alpha": self.alpha_value,
            "createdAt": self.creation_time,
            "lastUpdated": self.last_update_time,
            "dialogueHistory": self.dialogue_queue[-10:],  # Last 10 dialogues
            "animationQueue": [(anim.value, dur, loop) for anim, dur, loop in self.animation_queue]
        }

    def to_json(self) -> str:
        """Export character as JSON"""
        return json.dumps(self.to_dict(), indent=2)

    def from_json(self, json_str: str):
        """Load character state from JSON"""
        data = json.loads(json_str)
        self.position = Vector3(**data["position"])
        self.rotation = Rotation(**data["rotation"])
        self.scale = Vector3(**data["scale"])
        return self


class ALICEScene:
    """Scene containing ALICE and interactive elements"""

    def __init__(self, width: int = 1920, height: int = 1080, background: str = "#0a0e27"):
        self.width = width
        self.height = height
        self.background = background
        self.alice: Optional[ALICE3D] = None
        self.camera_position = Vector3(0, 1.7, 4)
        self.camera_target = Vector3(0, 1, 0)
        self.lights = {}
        self.interactive_objects = {}
        self.scene_created_time = datetime.now().isoformat()

    def add_alice(self, alice: ALICE3D):
        """Add ALICE to scene"""
        self.alice = alice
        return self

    def set_camera(self, x: float, y: float, z: float, target_x: float = 0, target_y: float = 1, target_z: float = 0):
        """Set camera position and target"""
        self.camera_position = Vector3(x, y, z)
        self.camera_target = Vector3(target_x, target_y, target_z)
        return self

    def add_light(self, name: str, light_type: str, x: float, y: float, z: float, intensity: float = 1.0):
        """Add light to scene"""
        self.lights[name] = {
            "type": light_type,
            "position": {"x": x, "y": y, "z": z},
            "intensity": intensity
        }
        return self

    def to_dict(self) -> Dict:
        """Export scene as dictionary"""
        return {
            "width": self.width,
            "height": self.height,
            "background": self.background,
            "camera": {
                "position": self.camera_position.to_dict(),
                "target": self.camera_target.to_dict()
            },
            "alice": self.alice.to_dict() if self.alice else None,
            "lights": self.lights,
            "createdAt": self.scene_created_time
        }

    def to_json(self) -> str:
        """Export scene as JSON"""
        return json.dumps(self.to_dict(), indent=2)


def create_alice_viewer_html(scene: ALICEScene) -> str:
    """Generate interactive HTML viewer for ALICE with Three.js"""
    scene_data = scene.to_dict()
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ALICE - Interactive 3D Character Viewer</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{ width: 100%; height: 100%; }}
        body {{
            font-family: 'Courier New', monospace;
            background: {scene_data['background']};
            color: #00ff88;
            overflow: hidden;
        }}
        #canvas {{ display: block; width: 100%; height: 100%; }}
        
        #ui {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(10, 14, 39, 0.95);
            padding: 20px;
            border-radius: 8px;
            font-size: 13px;
            max-width: 350px;
            border: 2px solid #00ff88;
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
        }}
        
        #stats {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(10, 14, 39, 0.95);
            padding: 15px;
            border-radius: 8px;
            font-size: 12px;
            border: 2px solid #00ff88;
            font-family: monospace;
        }}
        
        h1 {{
            color: #00ff88;
            font-size: 18px;
            margin-bottom: 15px;
            text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
        }}
        
        h2 {{
            color: #00ff88;
            margin: 15px 0 10px 0;
            font-size: 13px;
            border-bottom: 1px solid #00ff88;
            padding-bottom: 5px;
        }}
        
        .info-line {{
            margin: 5px 0;
            display: flex;
            justify-content: space-between;
        }}
        
        .label {{ color: #888; }}
        .value {{ color: #00ff88; font-weight: bold; }}
        
        .button-group {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin: 10px 0;
        }}
        
        button {{
            background: rgba(0, 255, 136, 0.2);
            border: 1px solid #00ff88;
            color: #00ff88;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            font-family: monospace;
            transition: all 0.3s;
            font-size: 12px;
        }}
        
        button:hover {{
            background: rgba(0, 255, 136, 0.4);
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
            transform: scale(1.05);
        }}
        
        button:active {{
            transform: scale(0.95);
        }}
        
        input[type="text"] {{
            background: rgba(0, 255, 136, 0.1);
            border: 1px solid #00ff88;
            color: #00ff88;
            padding: 6px;
            border-radius: 4px;
            width: 100%;
            margin: 5px 0;
            font-family: monospace;
            font-size: 12px;
        }}
        
        input[type="text"]:focus {{
            outline: none;
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
        }}
        
        .dialogue-box {{
            background: rgba(0, 255, 136, 0.1);
            border-left: 3px solid #00ff88;
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            max-height: 100px;
            overflow-y: auto;
        }}
    </style>
</head>
<body>
    <canvas id="canvas"></canvas>
    
    <div id="ui">
        <h1>🤖 ALICE - Interactive Character</h1>
        
        <h2>Character Status</h2>
        <div class="info-line">
            <span class="label">Name:</span>
            <span class="value" id="char-name">{scene_data['alice']['name']}</span>
        </div>
        <div class="info-line">
            <span class="label">Animation:</span>
            <span class="value" id="anim-type">{scene_data['alice']['currentAnimation']}</span>
        </div>
        <div class="info-line">
            <span class="label">Position:</span>
            <span class="value" id="position-info">0.0, 0.0, 0.0</span>
        </div>
        
        <h2>Animation Controls</h2>
        <div class="button-group">
            <button onclick="playAnim('idle')">IDLE</button>
            <button onclick="playAnim('walk')">WALK</button>
            <button onclick="playAnim('jump')">JUMP</button>
            <button onclick="playAnim('dance')">DANCE</button>
            <button onclick="playAnim('wave')">WAVE</button>
            <button onclick="playAnim('think')">THINK</button>
        </div>
        
        <h2>Dialogue</h2>
        <input type="text" id="dialogue-input" placeholder="What should ALICE say?">
        <button onclick="makeAliceTalk()" style="width: 100%; margin-top: 5px;">SAY</button>
        <div class="dialogue-box" id="dialogue-history"></div>
        
        <h2>Appearance</h2>
        <div class="button-group">
            <button onclick="changeColor('#00ff88')">Green</button>
            <button onclick="changeColor('#00ffff')">Cyan</button>
            <button onclick="changeColor('#ff00ff')">Magenta</button>
            <button onclick="changeColor('#ffff00')">Yellow</button>
        </div>
    </div>
    
    <div id="stats">
        <div class="info-line">
            <span class="label">FPS:</span>
            <span class="value" id="fps">60</span>
        </div>
        <div class="info-line">
            <span class="label">Polygons:</span>
            <span class="value" id="polys">0</span>
        </div>
        <div class="info-line">
            <span class="label">Time:</span>
            <span class="value" id="time-display">00:00</span>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script>
        const sceneData = {json.dumps(scene_data)};
        let aliceMesh = null;
        let currentAnimation = 'idle';
        let animationTime = 0;
        
        // Scene setup
        const canvas = document.getElementById('canvas');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(sceneData.background);
        
        const camera = new THREE.PerspectiveCamera(
            75, 
            window.innerWidth / window.innerHeight, 
            0.1, 
            1000
        );
        camera.position.set(
            sceneData.camera.position.x,
            sceneData.camera.position.y,
            sceneData.camera.position.z
        );
        camera.lookAt(
            sceneData.camera.target.x,
            sceneData.camera.target.y,
            sceneData.camera.target.z
        );
        
        const renderer = new THREE.WebGLRenderer({{ canvas, antialias: true, alpha: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFShadowShadowMap;
        
        // Lighting setup
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 15, 10);
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        directionalLight.shadow.camera.far = 50;
        directionalLight.castShadow = true;
        scene.add(directionalLight);
        
        // Ground
        const groundGeometry = new THREE.PlaneGeometry(100, 100);
        const groundMaterial = new THREE.MeshStandardMaterial({{ 
            color: '#1a2a4a',
            roughness: 0.8,
            metalness: 0.1
        }});
        const ground = new THREE.Mesh(groundGeometry, groundMaterial);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        scene.add(ground);
        
        // Create ALICE
        const aliceData = sceneData.alice;
        const geometry = new THREE.BoxGeometry(0.6, 1.8, 0.4);
        const material = new THREE.MeshStandardMaterial({{
            color: aliceData.material.color,
            metalness: aliceData.material.metalness,
            roughness: aliceData.material.roughness,
            emissive: '#003322'
        }});
        
        aliceMesh = new THREE.Mesh(geometry, material);
        aliceMesh.position.set(
            aliceData.position.x,
            aliceData.position.y,
            aliceData.position.z
        );
        aliceMesh.castShadow = true;
        aliceMesh.receiveShadow = true;
        scene.add(aliceMesh);
        
        // Animation functions
        function playAnim(anim) {{
            currentAnimation = anim;
            animationTime = 0;
            document.getElementById('anim-type').textContent = anim.toUpperCase();
            
            switch(anim) {{
                case 'jump':
                    aliceMesh.position.y = 2;
                    setTimeout(() => {{ aliceMesh.position.y = 0; }}, 600);
                    break;
                case 'wave':
                    aliceMesh.rotation.z += Math.PI / 6;
                    break;
                case 'dance':
                    let danceIntensity = 0;
                    let danceInterval = setInterval(() => {{
                        aliceMesh.rotation.y += 0.3;
                        aliceMesh.position.x = Math.sin(Date.now() / 200) * 0.5;
                        danceIntensity++;
                        if (danceIntensity > 30) clearInterval(danceInterval);
                    }}, 50);
                    break;
            }}
        }}
        
        function makeAliceTalk() {{
            const input = document.getElementById('dialogue-input');
            const text = input.value.trim();
            if (text.length > 0) {{
                currentAnimation = 'talk';
                const history = document.getElementById('dialogue-history');
                const entry = document.createElement('div');
                entry.style.marginBottom = '5px';
                entry.textContent = '> ' + text;
                history.appendChild(entry);
                history.scrollTop = history.scrollHeight;
                input.value = '';
            }}
        }}
        
        function changeColor(color) {{
            material.color.setHex(color.replace('#', '0x'));
        }}
        
        // Animation loop
        let frameCount = 0;
        let lastTime = Date.now();
        
        function animate() {{
            requestAnimationFrame(animate);
            
            animationTime += 0.016;
            
            // Simple animations
            if (currentAnimation === 'idle') {{
                aliceMesh.rotation.y = Math.sin(animationTime) * 0.1;
            }} else if (currentAnimation === 'walk') {{
                aliceMesh.position.x = Math.sin(animationTime) * 0.5;
                aliceMesh.rotation.y = Math.sin(animationTime) * 0.2;
            }} else if (currentAnimation === 'think') {{
                aliceMesh.rotation.x = Math.sin(animationTime * 2) * 0.05;
            }}
            
            // Update position info
            document.getElementById('position-info').textContent = 
                aliceMesh.position.x.toFixed(2) + ', ' +
                aliceMesh.position.y.toFixed(2) + ', ' +
                aliceMesh.position.z.toFixed(2);
            
            // FPS counter
            frameCount++;
            const now = Date.now();
            if (now - lastTime >= 1000) {{
                document.getElementById('fps').textContent = frameCount;
                frameCount = 0;
                lastTime = now;
            }}
            
            renderer.render(scene, camera);
        }}
        animate();
        
        // Handle window resize
        window.addEventListener('resize', () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});
        
        // Update time display
        setInterval(() => {{
            const now = new Date();
            const h = String(now.getHours()).padStart(2, '0');
            const m = String(now.getMinutes()).padStart(2, '0');
            document.getElementById('time-display').textContent = h + ':' + m;
        }}, 1000);
        
        // Allow Enter key to talk
        document.getElementById('dialogue-input').addEventListener('keypress', (e) => {{
            if (e.key === 'Enter') makeAliceTalk();
        }});
    </script>
</body>
</html>
'''
    return html


if __name__ == "__main__":
    # Create ALICE
    alice = ALICE3D(name="ALICE")
    alice.set_position(0, 0, 0)
    alice.set_material(color="#00ff88")
    
    # Create scene
    scene = ALICEScene(width=1920, height=1080)
    scene.add_alice(alice)
    scene.add_light("main", "directional", 10, 15, 10, 0.8)
    scene.add_light("fill", "point", -5, 5, 5, 0.4)
    
    # Generate HTML viewer
    html = create_alice_viewer_html(scene)
    
    print("✓ ALICE 3D Character System created")
    print(f"✓ Scene configuration saved")
    print(f"✓ HTML viewer ready")
