import { useEffect, useRef } from 'react'
import { apiFetch } from '../api'

interface RoomData {
  id: string
  name: string
  note: string
  x: number
  z: number
  w: number
  d: number
  links: Record<string, string>
}

const FALLBACK_ROOMS: RoomData[] = [
  { id: 'master_bedroom', name: 'Master Bedroom', note: 'Large upstairs bedroom on the west side of the house.', x: 12, z: 0, w: 9, d: 6, links: { east: 'master_bathroom', south: 'office_closet' } },
  { id: 'master_bathroom', name: 'Master Bathroom', note: 'Bathroom suite between the master bedroom and dining room.', x: 21, z: 0, w: 7, d: 2, links: { west: 'master_bedroom', east: 'dining_room', south: 'hallway_closet_upper_a' } },
  { id: 'hallway_closet_upper_a', name: 'Hallway Closet', note: 'Compact upstairs hallway closet below the master bathroom.', x: 21, z: 2, w: 3, d: 2, links: { north: 'master_bathroom', east: 'main_bathroom', south: 'hallway_closet_upper_b' } },
  { id: 'main_bathroom', name: 'Main Bathroom', note: 'Shared upstairs bathroom beside the central closets.', x: 24, z: 2, w: 4, d: 4, links: { west: 'hallway_closet_upper_a', south: 'upstairs_hallway' } },
  { id: 'hallway_closet_upper_b', name: 'Hallway Closet', note: 'Second small closet in the upstairs bath cluster.', x: 21, z: 4, w: 3, d: 2, links: { north: 'hallway_closet_upper_a', south: 'upstairs_hallway' } },
  { id: 'dining_room', name: 'Dining Room', note: 'Tall central upstairs room between bathrooms, kitchen, and stairs.', x: 28, z: 0, w: 7.5, d: 9, links: { west: 'master_bathroom', east: 'kitchen', south: 'upstairs_stairs' } },
  { id: 'kitchen', name: 'Kitchen', note: 'Upstairs kitchen connected to the dining and living spaces.', x: 35.5, z: 0, w: 8, d: 6.5, links: { west: 'dining_room', east: 'glass_room', south: 'living_room' } },
  { id: 'glass_room', name: 'Glass Room', note: 'Long eastern upstairs room with exterior exposure.', x: 43.5, z: 0, w: 6, d: 13, links: { west: 'kitchen' } },
  { id: 'office_closet', name: 'Office Closet', note: 'Small closet above Cody Office.', x: 12, z: 6, w: 4, d: 2, links: { north: 'master_bedroom', east: 'hallway_closet_upper_c', south: 'cody_office' } },
  { id: 'hallway_closet_upper_c', name: 'Hallway Closet', note: 'Closet segment west of the upstairs hallway.', x: 16, z: 6, w: 4, d: 2, links: { west: 'office_closet', east: 'upstairs_hallway', south: 'cody_office' } },
  { id: 'upstairs_hallway', name: 'Upstairs Hallway', note: 'Central upstairs connector for bedrooms, closets, bathrooms, and dining.', x: 20, z: 6, w: 8, d: 2, links: { west: 'hallway_closet_upper_c', east: 'dining_room', north: 'main_bathroom', south: 'george_bedroom' } },
  { id: 'cody_office', name: 'Cody Office', note: 'Upstairs office at the southwest part of the occupied layout.', x: 12, z: 8, w: 8, d: 5, links: { north: 'office_closet', east: 'george_bedroom' } },
  { id: 'george_bedroom', name: 'George Bedroom', note: 'Large bedroom below the upstairs hallway.', x: 20, z: 8, w: 8, d: 5, links: { north: 'upstairs_hallway', west: 'cody_office', east: 'hallway_closet_dining_a' } },
  { id: 'hallway_closet_dining_a', name: 'Hallway Closet', note: 'Closet stack below the dining room.', x: 28, z: 9, w: 3, d: 1.75, links: { north: 'dining_room', east: 'upstairs_stairs', south: 'hallway_closet_dining_b' } },
  { id: 'hallway_closet_dining_b', name: 'Hallway Closet', note: 'Lower closet beside the upstairs stairs.', x: 28, z: 10.75, w: 3, d: 2.25, links: { north: 'hallway_closet_dining_a', east: 'upstairs_stairs' } },
  { id: 'upstairs_stairs', name: 'Upstairs Stairs', note: 'Stairwell linking the upstairs and downstairs floor plans.', x: 31, z: 9, w: 4.5, d: 4, links: { west: 'hallway_closet_dining_a', north: 'dining_room', east: 'living_room', south: 'downstairs_stairs' } },
  { id: 'living_room', name: 'Living Room', note: 'Upstairs living room below the kitchen.', x: 35.5, z: 6.5, w: 8, d: 6.5, links: { north: 'kitchen', east: 'glass_room', west: 'upstairs_stairs' } },
  { id: 'garage', name: 'Garage', note: 'Large downstairs garage at the west side.', x: 0, z: 18, w: 12, d: 12, links: { east: 'music_room' } },
  { id: 'music_room', name: 'Music Room', note: 'Downstairs music room above the workout room.', x: 12, z: 18, w: 10, d: 7, links: { west: 'garage', east: 'harris_bathroom', south: 'workout_room' } },
  { id: 'workout_room', name: 'Workout Room', note: 'Downstairs room below the music room.', x: 12, z: 25, w: 10, d: 5, links: { north: 'music_room', east: 'amanda_office' } },
  { id: 'harris_bathroom', name: 'Harris Bathroom', note: 'Downstairs bathroom west of Harris Bedroom.', x: 22, z: 18, w: 4.5, d: 6, links: { west: 'music_room', east: 'harris_bedroom', south: 'downstairs_hallway' } },
  { id: 'harris_bedroom', name: 'Harris Bedroom', note: 'Large downstairs bedroom between bathroom and laundry.', x: 26.5, z: 18, w: 8.5, d: 6, links: { west: 'harris_bathroom', east: 'laundry_room', south: 'downstairs_hallway' } },
  { id: 'laundry_room', name: 'Laundry Room', note: 'Downstairs utility room beside the cellar and playroom.', x: 35, z: 18, w: 7.5, d: 6, links: { west: 'harris_bedroom', east: 'creepy_cellar', south: 'playroom' } },
  { id: 'creepy_cellar', name: 'Creepy Cellar', note: 'Long eastern downstairs cellar area.', x: 42.5, z: 18, w: 5.5, d: 12, links: { west: 'laundry_room' } },
  { id: 'downstairs_hallway', name: 'Downstairs Hallway', note: 'Downstairs hallway segment connecting bedrooms, offices, and stairs.', x: 22, z: 24, w: 13, d: 2, links: { north: 'harris_bathroom', east: 'playroom', south: 'amanda_office' } },
  { id: 'amanda_office', name: 'Amanda Office', note: 'Downstairs office near the stairwell.', x: 22, z: 26, w: 6, d: 4, links: { north: 'downstairs_hallway', west: 'workout_room', east: 'hallway_closet_downstairs' } },
  { id: 'hallway_closet_downstairs', name: 'Hallway Closet', note: 'Small downstairs closet beside Amanda Office.', x: 28, z: 26, w: 2.5, d: 2, links: { west: 'amanda_office', east: 'downstairs_stairs', south: 'amanda_office_closet' } },
  { id: 'amanda_office_closet', name: 'Amanda Office Closet', note: 'Closet below Amanda Office hallway closet.', x: 28, z: 28, w: 2.5, d: 2, links: { north: 'hallway_closet_downstairs', east: 'downstairs_stairs' } },
  { id: 'downstairs_stairs', name: 'Downstairs Stairs', note: 'Lower stairwell linking back to the upstairs stairs.', x: 30.5, z: 26, w: 4.5, d: 4, links: { west: 'hallway_closet_downstairs', east: 'playroom', north: 'downstairs_hallway', south: 'upstairs_stairs' } },
  { id: 'playroom', name: 'Playroom', note: 'Large downstairs playroom below the laundry room.', x: 35, z: 24, w: 7.5, d: 6, links: { north: 'laundry_room', west: 'downstairs_stairs', east: 'creepy_cellar' } },
]

const HOTSPOTS = [
  { id: 'kitchen_sensor', room: 'kitchen', label: 'Kitchen ceiling sensor', type: 'sensor', detail: 'Active sensor', x: 39.6, y: 2.5, z: 2.2 },
  { id: 'cellar_hazard', room: 'creepy_cellar', label: 'Cellar floor hazard', type: 'warning', detail: 'Low visibility zone', x: 45.2, y: 0.08, z: 24.4 },
  { id: 'glass_nest', room: 'glass_room', label: 'Bird nest with eggs', type: 'nest', detail: 'Protected area', x: 46.6, y: 2.35, z: 2.8 },
  { id: 'garage_equipment', room: 'garage', label: 'Garage equipment rack', type: 'equip', detail: 'Equipment', x: 2.1, y: 0.85, z: 20.8 },
  { id: 'stairs_inspect', room: 'upstairs_stairs', label: 'Stair inspection point', type: 'inspect', detail: 'Inspection point', x: 33.2, y: 1.05, z: 11.0 },
]

const PALETTE: Record<string, string> = {
  sensor: '#5db7ff',
  warning: '#f7b955',
  nest: '#5ee08b',
  equip: '#b69cff',
  inspect: '#ff6b5f',
}

const DIRECTIONS = ['north', 'east', 'south', 'west'] as const
type Direction = typeof DIRECTIONS[number]
const DIR_ANGLES: Record<Direction, number> = {
  north: Math.PI, east: Math.PI / 2, south: 0, west: -Math.PI / 2,
}
const SITE_BOUNDS = { minX: -8, minZ: -6, maxX: 57.5, maxZ: 36 }
const NEAR_PLANE = 0.04
const WALK_STEP = 0.095
const KEY_TURN_STEP = 0.026
const DRAG_TURN_STEP = 0.006

function WireframeVisualizer() {
  const sceneRef = useRef<HTMLCanvasElement>(null)
  const mapRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const roomNameRef = useRef<HTMLElement>(null)
  const roomNoteRef = useRef<HTMLParagraphElement>(null)
  const hotspotListRef = useRef<HTMLDivElement>(null)
  const compassRef = useRef<HTMLDivElement>(null)
  const roomsRef = useRef<RoomData[]>(FALLBACK_ROOMS)

  useEffect(() => {
    apiFetch<{ rooms: RoomData[] }>('/rooms')
      .then(data => {
        if (data.rooms?.length) {
          const vaultById = new Map(data.rooms.map(r => [r.id, r]))
          roomsRef.current = FALLBACK_ROOMS.map(r => vaultById.get(r.id) ?? r)
        }
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    const scene = sceneRef.current!
    const mapCanvas = mapRef.current!
    const ctx = scene.getContext('2d')!
    const mapCtx = mapCanvas.getContext('2d')!

    let currentRoomId = 'upstairs_hallway'
    let facing: Direction = 'east'
    let facingAngle = DIR_ANGLES[facing]
    let camX = 24, camZ = 7
    let selectedHotspotId = 'stairs_inspect'
    let pulse = 0
    const pressedKeys = new Set<string>()
    let shiftHeld = false
    let isDragging = false
    let lastDragX = 0
    let rafId = 0

    function roomById(id: string) { return roomsRef.current.find(r => r.id === id)! }
    function activeRoom() { return roomById(currentRoomId) }
    function roomCenter(r: RoomData) { return { x: r.x + r.w / 2, z: r.z + r.d / 2 } }
    function roomContaining(px: number, pz: number) {
      return roomsRef.current.find(r => px >= r.x && px <= r.x + r.w && pz >= r.z && pz <= r.z + r.d)
    }
    function inBounds(px: number, pz: number) {
      return px >= SITE_BOUNDS.minX && px <= SITE_BOUNDS.maxX && pz >= SITE_BOUNDS.minZ && pz <= SITE_BOUNDS.maxZ
    }
    function indoors(px: number, pz: number) { return Boolean(roomContaining(px, pz)) }

    function setCurrentRoom(id: string) {
      if (currentRoomId === id) return
      currentRoomId = id
      const h = HOTSPOTS.find(hs => hs.room === id)
      if (h) selectedHotspotId = h.id
      updateHud()
    }

    function resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      const w = scene.offsetWidth
      const h = scene.offsetHeight
      scene.width = Math.round(w * dpr)
      scene.height = Math.round(h * dpr)
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    }

    function camSpace(px: number, py: number, pz: number) {
      const dx = px - camX, dz = pz - camZ
      const cy = Math.cos(facingAngle), sy = Math.sin(facingAngle)
      return { side: dz * sy - dx * cy, depth: dx * sy + dz * cy, vertical: py - 1.45 }
    }
    function projectCam(side: number, depth: number, vertical: number) {
      if (depth <= NEAR_PLANE) return null
      const dpr = window.devicePixelRatio || 1
      const W = scene.width / dpr, H = scene.height / dpr
      const focal = Math.min(W, H) * 0.76
      const horizon = H * 0.44
      return { x: W / 2 + side * focal / depth, y: horizon - vertical * focal / depth, depth }
    }
    function project(px: number, py: number, pz: number) {
      const cs = camSpace(px, py, pz)
      return projectCam(cs.side, cs.depth, cs.vertical)
    }

    type CamPt = { side: number; depth: number; vertical: number }
    function intersectNear(a: CamPt, b: CamPt): CamPt {
      const t = (NEAR_PLANE - a.depth) / (b.depth - a.depth)
      return { side: a.side + (b.side - a.side) * t, depth: NEAR_PLANE, vertical: a.vertical + (b.vertical - a.vertical) * t }
    }
    function clipPolygon(pts: CamPt[]): CamPt[] {
      const out: CamPt[] = []
      for (let i = 0; i < pts.length; i++) {
        const cur = pts[i], prev = pts[(i + pts.length - 1) % pts.length]
        const curIn = cur.depth > NEAR_PLANE, prevIn = prev.depth > NEAR_PLANE
        if (curIn !== prevIn) out.push(intersectNear(prev, cur))
        if (curIn) out.push(cur)
      }
      return out
    }

    function drawLine3d(ax: number, ay: number, az: number, bx: number, by: number, bz: number, color = 'rgba(238,242,248,0.72)', width = 1) {
      let ca = camSpace(ax, ay, az), cb = camSpace(bx, by, bz)
      if (ca.depth <= NEAR_PLANE && cb.depth <= NEAR_PLANE) return
      if (ca.depth <= NEAR_PLANE) ca = intersectNear(cb, ca)
      else if (cb.depth <= NEAR_PLANE) cb = intersectNear(ca, cb)
      const pa = projectCam(ca.side, ca.depth, ca.vertical)
      const pb = projectCam(cb.side, cb.depth, cb.vertical)
      if (!pa || !pb) return
      ctx.strokeStyle = color; ctx.lineWidth = width
      ctx.beginPath(); ctx.moveTo(pa.x, pa.y); ctx.lineTo(pb.x, pb.y); ctx.stroke()
    }

    type Pt3 = { x: number; y: number; z: number }
    function drawPane3d(pts: Pt3[], fill: string) {
      const clipped = clipPolygon(pts.map(p => camSpace(p.x, p.y, p.z)))
      if (clipped.length < 3) return
      const projected = clipped.map(c => projectCam(c.side, c.depth, c.vertical))
      if (projected.some(p => !p)) return
      ctx.fillStyle = fill
      ctx.beginPath()
      ctx.moveTo(projected[0]!.x, projected[0]!.y)
      for (let i = 1; i < projected.length; i++) ctx.lineTo(projected[i]!.x, projected[i]!.y)
      ctx.closePath(); ctx.fill()
    }

    function avgDepth(pts: Pt3[]) {
      const depths = pts.map(p => project(p.x, p.y, p.z)?.depth).filter(Boolean) as number[]
      return depths.length ? depths.reduce((s, d) => s + d, 0) / depths.length : -Infinity
    }

    function drawRoom(room: RoomData) {
      const { x: x0, z: z0, w, d } = room
      const x1 = x0 + w, z1 = z0 + d, y0 = 0, y1 = 3
      const walls: Pt3[][] = [
        [{ x: x0, y: y0, z: z0 }, { x: x1, y: y0, z: z0 }, { x: x1, y: y1, z: z0 }, { x: x0, y: y1, z: z0 }],
        [{ x: x1, y: y0, z: z0 }, { x: x1, y: y0, z: z1 }, { x: x1, y: y1, z: z1 }, { x: x1, y: y1, z: z0 }],
        [{ x: x1, y: y0, z: z1 }, { x: x0, y: y0, z: z1 }, { x: x0, y: y1, z: z1 }, { x: x1, y: y1, z: z1 }],
        [{ x: x0, y: y0, z: z1 }, { x: x0, y: y0, z: z0 }, { x: x0, y: y1, z: z0 }, { x: x0, y: y1, z: z1 }],
      ]
      const paneFill = room.id === currentRoomId ? 'rgba(238,242,248,0.055)' : 'rgba(238,242,248,0.035)'
      walls.slice().sort((a, b) => avgDepth(b) - avgDepth(a)).forEach(w => drawPane3d(w, paneFill))

      const emphasis = room.id === currentRoomId ? 'rgba(238,242,248,0.86)' : 'rgba(238,242,248,0.25)'
      const lw = room.id === currentRoomId ? 1.8 : 1
      const edges: [Pt3, Pt3][] = [
        [{ x: x0, y: y0, z: z0 }, { x: x1, y: y0, z: z0 }], [{ x: x1, y: y0, z: z0 }, { x: x1, y: y0, z: z1 }],
        [{ x: x1, y: y0, z: z1 }, { x: x0, y: y0, z: z1 }], [{ x: x0, y: y0, z: z1 }, { x: x0, y: y0, z: z0 }],
        [{ x: x0, y: y1, z: z0 }, { x: x1, y: y1, z: z0 }], [{ x: x1, y: y1, z: z0 }, { x: x1, y: y1, z: z1 }],
        [{ x: x1, y: y1, z: z1 }, { x: x0, y: y1, z: z1 }], [{ x: x0, y: y1, z: z1 }, { x: x0, y: y1, z: z0 }],
        [{ x: x0, y: y0, z: z0 }, { x: x0, y: y1, z: z0 }], [{ x: x1, y: y0, z: z0 }, { x: x1, y: y1, z: z0 }],
        [{ x: x1, y: y0, z: z1 }, { x: x1, y: y1, z: z1 }], [{ x: x0, y: y0, z: z1 }, { x: x0, y: y1, z: z1 }],
      ]
      edges.forEach(([a, b]) => drawLine3d(a.x, a.y, a.z, b.x, b.y, b.z, emphasis, lw))
      for (let gx = x0 + 2; gx < x1; gx += 2) drawLine3d(gx, y0, z0, gx, y0, z1, 'rgba(238,242,248,0.13)', 1)
      for (let gz = z0 + 2; gz < z1; gz += 2) drawLine3d(x0, y0, gz, x1, y0, gz, 'rgba(238,242,248,0.13)', 1)
    }

    function drawOutdoorGrid() {
      const color = 'rgba(94,224,139,0.22)'
      for (let x = SITE_BOUNDS.minX; x <= SITE_BOUNDS.maxX; x += 2) {
        for (let z = SITE_BOUNDS.minZ; z < SITE_BOUNDS.maxZ; z += 2) {
          const z2 = Math.min(z + 2, SITE_BOUNDS.maxZ)
          if (!indoors(x, (z + z2) / 2)) drawLine3d(x, 0, z, x, 0, z2, color, 1)
        }
      }
      for (let z = SITE_BOUNDS.minZ; z <= SITE_BOUNDS.maxZ; z += 2) {
        for (let x = SITE_BOUNDS.minX; x < SITE_BOUNDS.maxX; x += 2) {
          const x2 = Math.min(x + 2, SITE_BOUNDS.maxX)
          if (!indoors((x + x2) / 2, z)) drawLine3d(x, 0, z, x2, 0, z, color, 1)
        }
      }
    }

    function drawDoorways() {
      roomsRef.current.forEach(room => {
        Object.entries(room.links).forEach(([dir, target]) => {
          if (room.id > target) return
          let cx = 0, cz = 0
          if (dir === 'east') { cx = room.x + room.w; cz = room.z + room.d / 2 }
          else if (dir === 'west') { cx = room.x; cz = room.z + room.d / 2 }
          else if (dir === 'south') { cx = room.x + room.w / 2; cz = room.z + room.d }
          else if (dir === 'north') { cx = room.x + room.w / 2; cz = room.z }
          else return
          const horiz = dir === 'north' || dir === 'south'
          const ax = horiz ? cx - 1.1 : cx, az = horiz ? cz : cz - 1.1
          const bx = horiz ? cx + 1.1 : cx, bz = horiz ? cz : cz + 1.1
          drawLine3d(ax, 0.02, az, bx, 0.02, bz, 'rgba(238,242,248,0.95)', 4)
          drawLine3d(ax, 2.1, az, bx, 2.1, bz, 'rgba(238,242,248,0.38)', 1)
        })
      })
    }

    function drawHotspot(hs: typeof HOTSPOTS[0]) {
      const p = project(hs.x, hs.y, hs.z)
      if (!p) return
      const color = PALETTE[hs.type]
      const isSelected = hs.id === selectedHotspotId
      const radius = (isSelected ? 11 : 7) + Math.sin(pulse / 18) * (isSelected ? 2.5 : 0.8)
      ctx.save()
      ctx.globalAlpha = hs.room === currentRoomId ? 1 : 0.32
      ctx.strokeStyle = color; ctx.fillStyle = color
      ctx.lineWidth = isSelected ? 2.5 : 1.5
      ctx.beginPath(); ctx.arc(p.x, p.y, radius, 0, Math.PI * 2); ctx.stroke()
      ctx.beginPath()
      ctx.moveTo(p.x - radius * 1.7, p.y); ctx.lineTo(p.x + radius * 1.7, p.y)
      ctx.moveTo(p.x, p.y - radius * 1.7); ctx.lineTo(p.x, p.y + radius * 1.7)
      ctx.stroke()
      if (isSelected) {
        ctx.font = '12px Inter, system-ui, sans-serif'
        ctx.textAlign = 'center'
        ctx.fillStyle = color
        ctx.fillText(hs.detail.toUpperCase(), p.x, p.y - radius - 12)
      }
      ctx.restore()
    }

    function distToCamera(room: RoomData) {
      const c = roomCenter(room)
      return Math.hypot(c.x - camX, c.z - camZ)
    }

    function drawScene() {
      const dpr = window.devicePixelRatio || 1
      const W = scene.width / dpr, H = scene.height / dpr
      ctx.clearRect(0, 0, W, H)
      ctx.fillStyle = '#080b10'; ctx.fillRect(0, 0, W, H)
      drawOutdoorGrid()
      roomsRef.current.slice().sort((a, b) => distToCamera(b) - distToCamera(a)).forEach(drawRoom)
      drawDoorways()
      HOTSPOTS.slice().sort((a, b) => {
        return (project(b.x, b.y, b.z)?.depth || 0) - (project(a.x, a.y, a.z)?.depth || 0)
      }).forEach(drawHotspot)
      ctx.strokeStyle = 'rgba(238,242,248,0.88)'; ctx.lineWidth = 1
      const horizon = H * 0.44
      ctx.beginPath()
      ctx.moveTo(W / 2 - 12, horizon); ctx.lineTo(W / 2 + 12, horizon)
      ctx.moveTo(W / 2, horizon - 12); ctx.lineTo(W / 2, horizon + 12)
      ctx.stroke()
    }

    function drawMap() {
      const pad = 32, bounds = SITE_BOUNDS
      const sx = (mapCanvas.width - pad * 2) / (bounds.maxX - bounds.minX)
      const sz = (mapCanvas.height - pad * 2) / (bounds.maxZ - bounds.minZ)
      const scale = Math.min(sx, sz)
      const tx = (x: number) => pad + (x - bounds.minX) * scale
      const tz = (z: number) => pad + (z - bounds.minZ) * scale
      mapCtx.clearRect(0, 0, mapCanvas.width, mapCanvas.height)
      mapCtx.fillStyle = '#0b0f16'; mapCtx.fillRect(0, 0, mapCanvas.width, mapCanvas.height)
      roomsRef.current.forEach(room => {
        mapCtx.lineWidth = room.id === currentRoomId ? 4 : 2
        mapCtx.strokeStyle = room.id === currentRoomId ? '#eef2f8' : 'rgba(238,242,248,0.28)'
        mapCtx.strokeRect(tx(room.x), tz(room.z), room.w * scale, room.d * scale)
        mapCtx.fillStyle = room.id === currentRoomId ? 'rgba(238,242,248,0.07)' : 'transparent'
        mapCtx.fillRect(tx(room.x), tz(room.z), room.w * scale, room.d * scale)
        mapCtx.fillStyle = 'rgba(238,242,248,0.62)'
        mapCtx.font = '10px Inter, system-ui, sans-serif'
        mapCtx.fillText(room.name, tx(room.x) + 8, tz(room.z) + 22)
      })
      HOTSPOTS.forEach(hs => {
        mapCtx.fillStyle = PALETTE[hs.type]
        mapCtx.globalAlpha = hs.id === selectedHotspotId ? 1 : 0.55
        mapCtx.beginPath()
        mapCtx.arc(tx(hs.x), tz(hs.z), hs.id === selectedHotspotId ? 8 : 5, 0, Math.PI * 2)
        mapCtx.fill()
      })
      mapCtx.globalAlpha = 1
      mapCtx.strokeStyle = '#eef2f8'; mapCtx.fillStyle = '#eef2f8'; mapCtx.lineWidth = 3
      mapCtx.beginPath(); mapCtx.arc(tx(camX), tz(camZ), 8, 0, Math.PI * 2); mapCtx.stroke()
      mapCtx.beginPath()
      mapCtx.moveTo(tx(camX), tz(camZ))
      mapCtx.lineTo(tx(camX + Math.sin(facingAngle) * 1.5), tz(camZ + Math.cos(facingAngle) * 1.5))
      mapCtx.stroke()
    }

    function updateHud() {
      const room = activeRoom()
      if (roomNameRef.current) roomNameRef.current.textContent = room.name
      if (roomNoteRef.current) roomNoteRef.current.textContent = room.note
      if (compassRef.current) compassRef.current.textContent = `Facing ${facing}`
      if (!hotspotListRef.current) return
      const relevant = HOTSPOTS.filter(hs => hs.room === currentRoomId)
      const nearby = relevant.length ? relevant : HOTSPOTS.filter(hs => hs.id === selectedHotspotId)
      hotspotListRef.current.innerHTML = ''
      nearby.forEach(hs => {
        const btn = document.createElement('button')
        btn.className = 'wfv-hotspot'
        btn.setAttribute('aria-pressed', String(hs.id === selectedHotspotId))
        btn.style.color = PALETTE[hs.type]
        btn.innerHTML = `<span class="wfv-dot"></span><span><b>${hs.label}</b>${hs.detail}</span>`
        btn.addEventListener('click', () => { selectedHotspotId = hs.id; drawScene(); drawMap() })
        hotspotListRef.current!.append(btn)
      })
    }

    function syncFacingLabel() {
      facing = DIRECTIONS.reduce((best, dir) => {
        const angDist = (a: number, b: number) => Math.abs(Math.atan2(Math.sin(a - b), Math.cos(a - b)))
        return angDist(facingAngle, DIR_ANGLES[dir]) < angDist(facingAngle, DIR_ANGLES[best]) ? dir : best
      }, DIRECTIONS[0])
      if (compassRef.current) compassRef.current.textContent = `Facing ${facing}`
    }

    function moveRoom(dir: string) {
      const room = activeRoom()
      const target = (room.links as Record<string, string>)[dir]
      if (target) {
        const dest = roomById(target)
        const c = roomCenter(dest)
        camX = c.x; camZ = c.z
        setCurrentRoom(target)
      }
      updateHud()
    }

    function rotate(delta: number) {
      const idx = DIRECTIONS.indexOf(facing)
      facing = DIRECTIONS[(idx + delta + DIRECTIONS.length) % DIRECTIONS.length]
      facingAngle = DIR_ANGLES[facing]
      updateHud()
    }

    function fluidMove(localForward: number, localRight = 0) {
      const nx = camX + Math.sin(facingAngle) * localForward * WALK_STEP - Math.cos(facingAngle) * localRight * WALK_STEP
      const nz = camZ + Math.cos(facingAngle) * localForward * WALK_STEP + Math.sin(facingAngle) * localRight * WALK_STEP
      if (!inBounds(nx, nz)) return false
      camX = nx; camZ = nz
      const room = roomContaining(camX, camZ)
      if (room && room.id !== currentRoomId) setCurrentRoom(room.id)
      return true
    }

    function dragTurn(px: number) {
      facingAngle -= px * DRAG_TURN_STEP
      syncFacingLabel()
      drawScene(); drawMap()
    }

    // Controls wiring
    const onControlClick = (e: Event) => {
      const btn = (e.target as HTMLElement).closest('[data-action]') as HTMLElement | null
      if (!btn) return
      const action = btn.dataset.action
      if (action === 'forward') { moveRoom(facing); drawScene(); drawMap() }
      if (action === 'back') { moveRoom(DIRECTIONS[(DIRECTIONS.indexOf(facing) + 2) % 4]); drawScene(); drawMap() }
      if (action === 'left') { rotate(-1); drawScene(); drawMap() }
      if (action === 'right') { rotate(1); drawScene(); drawMap() }
    }
    containerRef.current?.addEventListener('click', onControlClick)

    const onPointerDown = (e: PointerEvent) => {
      isDragging = true; lastDragX = e.clientX
      scene.classList.add('wfv-dragging')
      scene.setPointerCapture(e.pointerId)
      e.preventDefault()
    }
    const onPointerMove = (e: PointerEvent) => {
      if (!isDragging) return
      dragTurn(e.clientX - lastDragX)
      lastDragX = e.clientX
      e.preventDefault()
    }
    const endDrag = (e: PointerEvent) => {
      isDragging = false
      scene.classList.remove('wfv-dragging')
      if (scene.hasPointerCapture(e.pointerId)) scene.releasePointerCapture(e.pointerId)
    }
    scene.addEventListener('pointerdown', onPointerDown)
    scene.addEventListener('pointermove', onPointerMove)
    scene.addEventListener('pointerup', endDrag)
    scene.addEventListener('pointercancel', endDrag)

    const onKeyDown = (e: KeyboardEvent) => {
      const key = e.key.toLowerCase()
      shiftHeld = e.shiftKey
      if (e.key === 'ArrowUp') { moveRoom(facing); drawScene(); drawMap() }
      if (e.key === 'ArrowDown') { moveRoom(DIRECTIONS[(DIRECTIONS.indexOf(facing) + 2) % 4]); drawScene(); drawMap() }
      if (e.key === 'ArrowLeft') { rotate(-1); drawScene(); drawMap() }
      if (e.key === 'ArrowRight') { rotate(1); drawScene(); drawMap() }
      if (['w', 'a', 's', 'd'].includes(key)) {
        pressedKeys.add(key)
        e.preventDefault()
      }
    }
    const onKeyUp = (e: KeyboardEvent) => {
      pressedKeys.delete(e.key.toLowerCase())
      shiftHeld = e.shiftKey
    }
    window.addEventListener('keydown', onKeyDown)
    window.addEventListener('keyup', onKeyUp)

    // Size the root to exactly fill main-content (cancels its 40px padding on each side)
    // and reacts to sidebar expand/collapse via ResizeObserver on main-content.
    const root = containerRef.current!
    function applyFullBleed() {
      const mc = root.closest('.main-content') as HTMLElement | null
      if (mc) {
        root.style.width = mc.clientWidth + 'px'
        root.style.marginLeft = '-40px'
      }
      resize()
      drawScene()
      drawMap()
    }

    const onResize = applyFullBleed
    window.addEventListener('resize', onResize)
    const ro = new ResizeObserver(applyFullBleed)
    ro.observe(scene)
    const mainContent = root.closest('.main-content')
    if (mainContent) ro.observe(mainContent)

    function animate() {
      pulse++
      const fwd = (pressedKeys.has('w') ? 1 : 0) - (pressedKeys.has('s') ? 1 : 0)
      const sideIntent = (pressedKeys.has('d') ? 1 : 0) - (pressedKeys.has('a') ? 1 : 0)
      const strafe = shiftHeld ? sideIntent : 0
      const turn = shiftHeld ? 0 : sideIntent
      let moved = fwd !== 0 || strafe !== 0 ? fluidMove(fwd, strafe) : false
      if (turn !== 0) { facingAngle -= turn * KEY_TURN_STEP; syncFacingLabel(); moved = true }
      drawScene()
      if (moved) drawMap()
      rafId = requestAnimationFrame(animate)
    }

    applyFullBleed()
    updateHud()
    rafId = requestAnimationFrame(animate)

    return () => {
      cancelAnimationFrame(rafId)
      window.removeEventListener('keydown', onKeyDown)
      window.removeEventListener('keyup', onKeyUp)
      window.removeEventListener('resize', onResize)
      scene.removeEventListener('pointerdown', onPointerDown)
      scene.removeEventListener('pointermove', onPointerMove)
      scene.removeEventListener('pointerup', endDrag)
      scene.removeEventListener('pointercancel', endDrag)
      containerRef.current?.removeEventListener('click', onControlClick)
      ro.disconnect()
    }
  }, [])

  return (
    <>
      <style>{`
        .wfv-root {
          position: relative;
          /* width and margin-left set by JS (applyFullBleed) to fill main-content exactly */
          height: calc(100vh - 188px);
          min-height: 480px;
          background: #080b10;
          border-radius: 0;
          overflow: hidden;
          font-family: Inter, ui-sans-serif, system-ui, sans-serif;
        }
        .wfv-scene {
          display: block;
          width: 100%;
          height: 100%;
          cursor: grab;
          touch-action: none;
        }
        .wfv-scene.wfv-dragging { cursor: grabbing; }
        .wfv-compass {
          position: absolute;
          left: 50%;
          top: 18px;
          transform: translateX(-50%);
          padding: 8px 12px;
          border: 1px solid rgba(238,242,248,0.22);
          border-radius: 999px;
          background: rgba(12,16,24,0.86);
          color: #9aa6b7;
          font-size: 12px;
          pointer-events: none;
          backdrop-filter: blur(12px);
        }
        .wfv-hud {
          position: absolute;
          inset: 16px;
          display: grid;
          grid-template-columns: minmax(200px, 260px) 1fr minmax(200px, 280px);
          grid-template-rows: auto 1fr auto;
          gap: 14px;
          pointer-events: none;
        }
        .wfv-panel {
          pointer-events: auto;
          background: rgba(12,16,24,0.86);
          border: 1px solid rgba(238,242,248,0.22);
          backdrop-filter: blur(12px);
          box-shadow: 0 20px 60px rgba(0,0,0,0.34);
          padding: 14px;
          border-radius: 8px;
        }
        .wfv-title { grid-column: 1; grid-row: 1; }
        .wfv-title h2 { margin: 0 0 6px; font-size: 16px; line-height: 1.2; color: #eef2f8; }
        .wfv-title p { margin: 0; font-size: 12px; color: #9aa6b7; line-height: 1.4; }
        .wfv-status { grid-column: 1; grid-row: 2; align-self: start; }
        .wfv-status-label { margin: 0 0 10px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.12em; color: #9aa6b7; }
        .wfv-room-name { display: block; margin-bottom: 4px; font-size: 22px; font-weight: 700; line-height: 1; color: #eef2f8; }
        .wfv-room-note { margin: 0; font-size: 12px; color: #9aa6b7; line-height: 1.4; }
        .wfv-hotspot-list { display: grid; gap: 8px; margin-top: 12px; }
        .wfv-hotspot {
          display: grid;
          grid-template-columns: 12px 1fr;
          gap: 8px;
          align-items: start;
          width: 100%;
          padding: 8px;
          border: 1px solid rgba(238,242,248,0.22);
          border-radius: 6px;
          text-align: left;
          background: rgba(19,25,36,0.62);
          cursor: pointer;
          font-family: inherit;
          font-size: 12px;
          color: inherit;
        }
        .wfv-hotspot[aria-pressed="true"] {
          border-color: #eef2f8;
          background: rgba(30,38,54,0.96);
        }
        .wfv-dot {
          width: 10px; height: 10px; margin-top: 4px;
          border-radius: 50%; background: currentColor;
          box-shadow: 0 0 0 4px color-mix(in srgb, currentColor 18%, transparent);
        }
        .wfv-hotspot b { display: block; margin-bottom: 2px; font-size: 13px; color: #eef2f8; }
        .wfv-minimap { grid-column: 3; grid-row: 1 / span 2; align-self: start; }
        .wfv-minimap-label { margin: 0 0 10px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.12em; color: #9aa6b7; }
        .wfv-map {
          display: block; width: 100%;
          aspect-ratio: 1.1;
          border: 1px solid rgba(238,242,248,0.22);
          background: rgba(8,11,16,0.72);
          border-radius: 6px;
        }
        .wfv-legend {
          pointer-events: auto;
          grid-column: 2; grid-row: 3;
          align-self: end; justify-self: center;
          display: flex; flex-wrap: wrap; justify-content: center; gap: 10px;
          max-width: min(720px, 100%);
          padding: 10px 12px;
          border-radius: 8px;
          font-size: 12px;
          color: #9aa6b7;
          background: rgba(12,16,24,0.86);
          border: 1px solid rgba(238,242,248,0.22);
          backdrop-filter: blur(12px);
        }
        .wfv-legend-item { display: inline-flex; gap: 7px; align-items: center; white-space: nowrap; }
        .wfv-swatch { width: 13px; height: 13px; border: 1px solid currentColor; border-radius: 3px; flex-shrink: 0; }
        .wfv-controls {
          pointer-events: auto;
          grid-column: 1 / span 3; grid-row: 3;
          align-self: end; justify-self: start;
          display: grid;
          grid-template-columns: 64px 64px 64px;
          grid-template-rows: 42px 42px;
          gap: 8px; padding: 10px;
          border-radius: 8px;
          background: rgba(12,16,24,0.86);
          border: 1px solid rgba(238,242,248,0.22);
          backdrop-filter: blur(12px);
        }
        .wfv-controls button {
          border: 1px solid #eef2f8;
          background: rgba(19,25,36,0.78);
          color: #eef2f8;
          border-radius: 6px;
          font-size: 20px;
          line-height: 1;
          cursor: pointer;
        }
        .wfv-controls button:hover { background: rgba(40,50,72,0.9); }
        .wfv-btn-fwd { grid-column: 2; }
        .wfv-btn-left { grid-column: 1; grid-row: 2; }
        .wfv-btn-back { grid-column: 2; grid-row: 2; }
        .wfv-btn-right { grid-column: 3; grid-row: 2; }
      `}</style>
      <div className="wfv-root" ref={containerRef}>
        <canvas className="wfv-scene" ref={sceneRef} aria-label="3D wireframe building view" />
        <div className="wfv-compass" ref={compassRef}>Facing east</div>
        <section className="wfv-hud" aria-label="Visualizer controls and status">
          <div className="wfv-panel wfv-title">
            <h2>Wireframe Building Visualizer</h2>
            <p>Use arrow keys or buttons to move room-to-room. WASD moves fluidly. Drag to look around.</p>
          </div>

          <div className="wfv-panel wfv-status">
            <p className="wfv-status-label">Current Room</p>
            <strong className="wfv-room-name" ref={roomNameRef}>Upstairs Hallway</strong>
            <p className="wfv-room-note" ref={roomNoteRef}>Central upstairs connector for bedrooms, closets, bathrooms, and dining.</p>
            <div className="wfv-hotspot-list" ref={hotspotListRef} aria-label="Highlighted objects" />
          </div>

          <div className="wfv-panel wfv-minimap">
            <p className="wfv-minimap-label">Floor Plan</p>
            <canvas className="wfv-map" ref={mapRef} width={520} height={470} aria-label="Top-down map" />
          </div>

          <nav className="wfv-controls" aria-label="Navigation controls">
            <button className="wfv-btn-fwd" type="button" data-action="forward" aria-label="Move forward">↑</button>
            <button className="wfv-btn-left" type="button" data-action="left" aria-label="Turn left">↺</button>
            <button className="wfv-btn-back" type="button" data-action="back" aria-label="Move backward">↓</button>
            <button className="wfv-btn-right" type="button" data-action="right" aria-label="Turn right">↻</button>
          </nav>

          <aside className="wfv-legend" aria-label="Highlight legend">
            <span className="wfv-legend-item"><i className="wfv-swatch" style={{ color: PALETTE.sensor }} />Active sensor</span>
            <span className="wfv-legend-item"><i className="wfv-swatch" style={{ color: PALETTE.warning }} />Hazard</span>
            <span className="wfv-legend-item"><i className="wfv-swatch" style={{ color: PALETTE.nest }} />Nest with eggs</span>
            <span className="wfv-legend-item"><i className="wfv-swatch" style={{ color: PALETTE.equip }} />Equipment</span>
            <span className="wfv-legend-item"><i className="wfv-swatch" style={{ color: PALETTE.inspect }} />Inspection point</span>
          </aside>
        </section>
      </div>
    </>
  )
}

export default Object.assign(WireframeVisualizer, { fullBleed: true })
