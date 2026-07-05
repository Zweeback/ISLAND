# GTA Dortmund - Unified Game Simulation

**Merged from**: `Zweeback/GTA` + `Zweeback/DORTMUND-GTA`  
**Type**: 2D/3D Urban Simulation  
**Platform**: AI Studio (Gemini)  
**Status**: Active development

---

## Overview

GTA Dortmund is a unified urban simulation sandbox that combines:
- **2D mode**: Top-down city overview, traffic flow, NPC patterns
- **3D mode**: Full 3D city rendering with immersive exploration
- **AI agents**: Simulated citizens, traffic, environmental systems
- **Data-driven**: Real Dortmund data (OpenData + local sources)

---

## Project Structure

```
PROJECTS/gta-dortmund/
├── src/
│   ├── scenes/               # 2D & 3D scene management
│   ├── simulation/           # Agent systems, physics
│   ├── rendering/            # Three.js canvas & visualization
│   ├── data/                 # Data loading & processing
│   ├── agents/               # NPC AI behavior
│   └── index.ts
├── public/                   # Static files
├── assets/                   # Project-specific models
├── config.json               # Project configuration
├── package.json              # Dependencies
├── .env.local                # API keys (GEMINI_API_KEY)
├── README.md                 # This file
└── ORIGINAL_REPOS.md         # Reference to original repos
```

---

## What's Inside

### From `Zweeback/GTA`
- Core AI Studio application scaffold
- Gemini API integration
- Node.js runtime setup
- Base UI framework

### From `Zweeback/DORTMUND-GTA`
- Dortmund-specific data models
- City geometry & streets
- Real-world data integration
- Localized content

### Merged Into
- **Unified codebase** in PROJECTS/gta-dortmund/
- **Single package.json** for dependencies
- **Combined assets** in 07_3D_ASSET_LIBRARY/
- **Shared config** with Jules integration

---

## Running the Game

### Local Development

```bash
cd ISLAND/PROJECTS/gta-dortmund

# 1. Install dependencies
npm install

# 2. Set your Gemini API key
echo "GEMINI_API_KEY=your_api_key_here" > .env.local

# 3. Start development server
npm run dev

# 4. Open browser
# → http://localhost:3000
```

### Build for Production

```bash
npm run build
npm start
```

---

## Integration with ISLAND

### Shared Assets
```
Needs 3D models?
└→ ISLAND/07_3D_ASSET_LIBRARY/
   ├── models/buildings/
   ├── models/vehicles/
   └── models/pedestrians/
```

### Knowledge Base
```
Need Dortmund data?
└→ ISLAND/05_RAG_SOURCE_OF_TRUTH/
   ├── dortmund_streets.json
   ├── population_data.csv
   ├── traffic_patterns.json
   └── historical_documents/
```

### Tools & Scrapers
```
Need real-time data?
└→ ISLAND/08_TOOLS_SCRIPTS/
   ├── scrapers/opendata_dortmund.py
   ├── scrapers/digibib.py
   └── tools/data_processor.py
```

### Jules Orchestration
```
Jules can trigger the game:
└→ JULES.trigger_app("gta-dortmund", "simulate", {
     "scenario": "rush_hour",
     "agents": 500,
     "duration": "5min"
   })
```

---

## Data Sources

### Real Dortmund Data (OpenData)
- Street networks (OpenStreetMap)
- Public amenities (OpenData Dortmund API)
- Population demographics
- Traffic patterns
- Historical information

### Game Data
- NPC behaviors
- Traffic rules
- Environmental effects
- Simulation parameters

---

## Game Modes

### Sandbox Mode
- Free exploration of Dortmund
- Spawn NPCs & vehicles
- Modify traffic rules
- Test scenarios

### Simulation Mode
- Run urban simulations
- Monitor agent behavior
- Analyze traffic flow
- Generate reports

### Data Analysis Mode
- Query RAG for Dortmund data
- Visualize statistics
- Compare patterns
- Export datasets

---

## Simulation Features

### AI Agents
- **Pedestrians**: Walk streets, shop, socialize
- **Drivers**: Navigate traffic, follow rules, handle accidents
- **Vendors**: Run shops, serve customers
- **Emergency**: Police, fire, ambulance responses

### Environment
- **Dynamic weather**
- **Day/night cycles**
- **Traffic lights & signs**
- **Accidents & events**

### Physics
- Collision detection
- Movement constraints
- Vehicle dynamics
- Physics-based interactions

---

## Configuration

Edit `config.json` to customize:

```json
{
  "id": "gta-dortmund",
  "name": "GTA Dortmund",
  "version": "1.0.0",
  "rendering": {
    "mode": "3d",
    "quality": "high",
    "fps": 60
  },
  "simulation": {
    "agents": 1000,
    "speed": 1.0,
    "weather": "dynamic"
  },
  "data_sources": {
    "rag": true,
    "opendata": true,
    "local_files": true
  }
}
```

---

## API Endpoints

### Game Control
```
POST /api/simulate/start
POST /api/simulate/stop
POST /api/simulate/reset
GET /api/simulate/status
```

### Data Queries
```
GET /api/data/streets
GET /api/data/amenities
GET /api/data/statistics
POST /api/data/query
```

### Jules Integration
```
POST /api/agents/trigger
GET /api/agents/status
POST /api/agents/command
```

---

## Original Repositories

- **GTA**: https://github.com/Zweeback/GTA
- **DORTMUND-GTA**: https://github.com/Zweeback/DORTMUND-GTA

Both have been consolidated into this unified project.

---

## Next Steps

- [ ] Test merged codebase
- [ ] Verify all dependencies work
- [ ] Load Dortmund data into RAG
- [ ] Connect Jules orchestration
- [ ] Deploy test build
- [ ] Document API endpoints

---

**Last Updated**: 2026-07-05  
**Status**: Merge in progress
