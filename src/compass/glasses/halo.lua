-- compass halo.lua — minimal on-device reflex app (ADR 0009 Decision §2).
-- PRE-HARDWARE SKETCH: never run on a device. Written against
-- docs/inspection/2026-08-19-halo-firmware-protocol.md (halo-firmware main @
-- 9a306ae7072d84a94f377e1b857d47d30ddaf014). "§n.n" cites PROTOCOL.md of that
-- revision; the halo == frame alias is per LUA_RUNTIME.md §API Modules.
-- Uploaded as main.lua and started by HaloGlasses.connect() (halo.py).
--
-- DIVERGENCE from ADR 0009 §2: retro trigger is DOUBLE-TAP, not a >500 ms
-- button hold. The documented long-press is only a 1 s hold released before
-- 2 s; holds >=2 s are firmware-reserved (2 s deep sleep, 5 s pairing, 15 s
-- ship mode) per §7.4 and BUTTON_LED_GUIDE §Quick Reference. The inspection
-- report recommends double-tap as the safer retro trigger.
--
-- Camera/audio ARE relayed here: the firmware exposes no Lua API that writes
-- the Video/Audio TX characteristics, so there is no host-direct path for
-- them on the custom channels (report §Gaps Q1) — Lua-pumped bluetooth.send
-- is the documented flow (§7.5/§7.9/§7.11). Alternative for mic on hardware
-- day: the standard LE Audio BAP source stream is host-direct and PREEMPTS
-- frame.microphone (§3.1.3).
--
-- TODO(hardware) list:
--   1. Callback registration shape for frame.button.single/double (§7.4) and
--      frame.imu.tap_callback (§7.6) — names documented, exact call shape not.
--   2. camera.capture cfg key names/values (§7.11 documents resolution=640 and
--      quality VERY_HIGH..LOW, not the exact table keys).
--   3. camera.read end-of-data convention (nil vs empty string) and whether
--      the end-of-image sentinel below matches what RxPhoto treats as final.
--   4. How to CLEAR previously drawn text — §7.10 documents only direct draws
--      (display.show is a no-op); no clear/fill API is documented.
--   5. Idle cadence: frame.yield() vs a short sleep (§7.1) — power vs latency.
--   6. Whether brilliant-msg's send_message() delivers the msg code as byte 1
--      of the receive_callback payload (assumed; frame-msg lineage).
--   7. Host->device messages larger than one MTU need app-side reassembly
--      (§2.1) — compass text messages are assumed single-chunk.
--   8. Mic first-read latency after start(), and pcm/16k/16-bit params (§7.9).

-- Message codes — MUST mirror halo.py's MSG_* constants (compass-defined
-- framing; see report "Lua runtime surface": compass defines its own framing).
local MSG_TEXT = 0x0a       -- host -> device: "RRGGBB\nline1\nline2"
local MSG_CAPTURE = 0x0d    -- host -> device: 1 quality byte
local MSG_AUDIO_CTL = 0x30  -- host -> device: 0x01 mic on / 0x00 mic off
local MSG_TAP = 0x09        -- device -> host: tap kind bytes (RxTap)
local MSG_PHOTO = 0x07      -- device -> host: JPEG chunks (RxPhoto)
local MSG_AUDIO = 0x05      -- device -> host: mic chunks (RxAudio)

local QUALITIES = { "VERY_HIGH", "HIGH", "MEDIUM", "LOW" }  -- §7.11 order = halo.py

local pending_quality = nil  -- set by MSG_CAPTURE, consumed by the main loop
local mic_on = false

local function send(code, payload)
  -- Device-side sends are capped at MTU-1 (§7.5 bluetooth.send/max_length);
  -- callers chunk, we just prefix the compass msg code.
  frame.bluetooth.send(string.char(code) .. (payload or ""))
end

local function render(rgb, line1, line2)
  -- Direct draws on the ~256x256 logical canvas, color is 0xRRGGBB per call;
  -- display.show() is a no-op (§7.10). Dogica 8px = 30 chars/line (SDK docs).
  frame.display.text(line1, 1, 104, rgb)                 -- §7.10
  if line2 and line2 ~= "" then
    frame.display.text(line2, 1, 128, 0xa0a0a0)          -- grey, matches mock
  end
end

local function on_data(payload)
  local code = string.byte(payload, 1)  -- TODO(hardware) #6: framing offset
  local body = string.sub(payload, 2)
  if code == MSG_TEXT then
    local hex, l1, l2 = string.match(body, "^(%x%x%x%x%x%x)\n([^\n]*)\n?(.*)$")
    render(tonumber(hex or "F0F0F0", 16), l1 or "", l2 or "")
  elseif code == MSG_CAPTURE then
    pending_quality = QUALITIES[(string.byte(body, 1) or 2) + 1] or "MEDIUM"
  elseif code == MSG_AUDIO_CTL then
    if string.byte(body, 1) == 1 and not mic_on then
      -- §7.9: pcm/lc3, 8/16 kHz; pcm 16 kHz 16-bit matches LaptopMicBuffer.
      frame.microphone.start { encoder = "pcm", sample_rate = 16000, bit_depth = 16 }
      mic_on = true
    elseif string.byte(body, 1) == 0 and mic_on then
      frame.microphone.stop()  -- §7.9
      mic_on = false
    end
  end
end

local function pump_camera()
  frame.camera.power_save(false)  -- must wake camera before capture (§7.11)
  -- Only resolution=640 is supported today (§7.11). TODO(hardware) #2: keys.
  frame.camera.capture { resolution = 640, quality = pending_quality }
  while not frame.camera.image_ready() do frame.yield() end  -- §7.11 poll
  local max = frame.bluetooth.max_length() - 1  -- room for our code byte (§7.5)
  while true do
    local chunk = frame.camera.read(max)  -- complete JPEG data, chunked (§7.11)
    if chunk == nil or #chunk == 0 then break end  -- TODO(hardware) #3
    send(MSG_PHOTO, chunk)
  end
  -- An empty bluetooth.send("") transmits nothing (§7.5), so end-of-image
  -- needs a real sentinel byte. TODO(hardware) #3: align with RxPhoto.
  send(MSG_PHOTO, "\x00")
  pending_quality = nil
end

local function pump_mic()
  -- Non-blocking: empty string until the first DMA block; partial reads OK
  -- (§7.9). Chunk cap as in pump_camera.
  local chunk = frame.microphone.read(frame.bluetooth.max_length() - 1)
  if chunk ~= nil and #chunk > 0 then send(MSG_AUDIO, chunk) end
end

local function notify(kind)
  -- Halo tap kinds go to the host as payload bytes (brilliant-msg CHANGELOG).
  send(MSG_TAP, kind)
end

-- Event wiring. TODO(hardware) #1: registration shape for all three.
frame.button.single(function() notify("single") end)   -- §7.4
frame.button.double(function() notify("double") end)   -- §7.4
frame.imu.tap_callback(function(kind)                  -- §7.6: 'single'/'double'/'triple'
  if kind == "single" or kind == "double" then notify(kind) end
end)
frame.bluetooth.receive_callback(on_data)              -- §7.5

frame.stay_awake(true)  -- active session; §7.1 / PM_SLEEP.md
-- Runs at boot AND after light_sleep() restarts main.lua from the top
-- (§7.1; check frame.wakeup_source() later if resume needs different UI).
render(0x78c8dc, "compass ready", "")

-- Event loop: callbacks fire between iterations (report "Lua runtime
-- surface": main.lua is an event loop, not linear code).
while true do
  if pending_quality then pump_camera() end
  if mic_on then pump_mic() end
  frame.yield()  -- §7.1; TODO(hardware) #5
end
