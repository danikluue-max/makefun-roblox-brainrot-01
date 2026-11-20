-- Brainrot Bay — server.
-- One job: own the whole game loop. The client only draws the HUD and asks;
-- every number, every transfer and every event is decided here.
--
-- Loop, in order:
--   1. Conveyor: a brainrot rolls out every few seconds, walks the lane, despawns.
--   2. Buy: walk up, click it (or the shop card), pay, carry it home.
--   3. Dock: step onto your base while carrying and it starts earning $/s.
--   4. Steal: click a brainrot on someone else's base; a 3s channel the owner
--      can break by coming home. A locked base cannot be stolen from.
--   5. Wave: every few minutes a tsunami sweeps the map; anyone outside
--      their base when it passes drops what they are carrying.
--   6. Rebirth: $50,000 + a Mythic owned resets your money for a permanent
--      +100% income multiplier (stacks).
--   7. Quests (round 3): buy 3 / steal 1 / survive a wave, each paying a
--      one-time cash reward the player claims from the HUD.
--   8. Prize book (round 3): every character ever docked is recorded in
--      the player's collection (found set), shown as a 36-cell grid.
--
-- Money and rebirths are saved with DataStoreService (pcall-guarded, so a
-- Studio without API access still plays fine).
--
-- Layout: small tables group the pieces — Util (position helpers), Bases
-- (the 8 base models), Sync (everything pushed to clients), Store (saves),
-- Conveyor (the lane), and the Actions tryBuy / trySteal / dockCarried.
-- bindRemotes and bindPlayers wire the events; the loops at the bottom
-- drive income, spawning, movement, autosave and the wave.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local DataStoreService = game:GetService("DataStoreService")

local BrainrotData = require(ReplicatedStorage.Shared.BrainrotData)
local CharacterFactory = require(ReplicatedStorage.Shared.CharacterFactory)
local FormatUtil = require(ReplicatedStorage.Shared.FormatUtil)

local Remotes = ReplicatedStorage:WaitForChild("Remotes")
local E = BrainrotData.ECONOMY

-- Quests (round 3): three earnable goals, each paying a one-time cash
-- reward the player claims from the HUD. Progress lives in playerData
-- and is saved with the rest of the profile.
local QUESTS = {
	{ id = "buy3", name = "Buy 3 brainrots", target = 3, reward = 500 },
	{ id = "steal1", name = "Steal 1 brainrot", target = 1, reward = 1500 },
	{ id = "wave1", name = "Survive a tsunami", target = 1, reward = 1000 },
}

local function questProgress(d, questId)
	if questId == "buy3" then
		return d.quests.bought
	elseif questId == "steal1" then
		return d.quests.stolen
	elseif questId == "wave1" then
		return d.quests.waves
	end
	return 0
end

local store = nil
pcall(function()
	store = DataStoreService:GetDataStore("BrainrotBay_v1")
end)

-- ---------------------------------------------------------------- state
local playerData = {} -- [Player] = { money, rebirths, baseIndex, owned, carrying, lockUntil, lockCooldownUntil, found, quests }
local baseOwner = {} -- [baseIndex] = Player
local lane = {} -- array of { id, model, spec, mutation, x }
local laneSeq = 0
local waveClock = 0

-- ---------------------------------------------------------------- Util
-- Position helpers shared by buy / steal / dock / wave checks.
local Util = {}

-- The part every distance check starts from; nil when the player has no
-- character loaded yet (joining, respawning).
function Util.rootPart(player)
	local char = player.Character
	return char and char:FindFirstChild("HumanoidRootPart")
end

function Util.distance(a, b)
	return (a - b).Magnitude
end

-- ---------------------------------------------------------------- Bases
local Bases = {}

function Bases.model(index)
	return workspace:FindFirstChild("Base" .. tostring(index))
end

function Bases.center(index)
	-- Bases sit on a ring of radius 105; the generator wrote the same math.
	local ang = math.rad(22.5 + 45 * (index - 1))
	return Vector3.new(105 * math.cos(ang), 0, 105 * math.sin(ang))
end

function Bases.sign(index, text)
	local base = Bases.model(index)
	if not base then
		return
	end
	local sign = base:FindFirstChild("Sign")
	if not sign then
		return
	end
	for _, guiName in ipairs({ "FrontGui", "BackGui" }) do
		local gui = sign:FindFirstChild(guiName)
		local label = gui and gui:FindFirstChild("Label")
		if label then
			label.Text = text
		end
	end
end

function Bases.setLockBeam(index, locked)
	local base = Bases.model(index)
	if not base then
		return
	end
	local beam = base:FindFirstChild("LockBeam")
	if beam then
		beam.Color = locked and Color3.fromRGB(220, 38, 38) or Color3.fromRGB(34, 197, 94)
	end
end

local function inOwnBase(player)
	local d = playerData[player]
	if not d or not d.baseIndex then
		return false
	end
	local root = Util.rootPart(player)
	if not root then
		return false
	end
	local c = Bases.center(d.baseIndex)
	local dx = root.Position.X - c.X
	local dz = root.Position.Z - c.Z
	return (dx * dx + dz * dz) < (13 * 13)
end

-- ---------------------------------------------------------------- Sync
-- Every push to a client goes through here, so the server never fires a
-- RemoteEvent from game logic directly.
local Sync = {}

local function notify(player, text, kind)
	Remotes.NotifyClient:FireClient(player, text, kind or "info")
end

local function incomePerSecond(d)
	local sum = 0
	for _, entry in pairs(d.owned) do
		sum += entry.rate
	end
	return sum * (1 + d.rebirths * E.rebirthMult)
end

function Sync.pushMoney(player)
	local d = playerData[player]
	if not d then
		return
	end
	local ls = player:FindFirstChild("leaderstats")
	local moneyValue = ls and ls:FindFirstChild("Money")
	if moneyValue then
		moneyValue.Value = math.floor(d.money)
	end
	local rebirthValue = ls and ls:FindFirstChild("Rebirths")
	if rebirthValue then
		rebirthValue.Value = d.rebirths
	end
	Remotes.MoneyUpdate:FireClient(player, math.floor(d.money), incomePerSecond(d))
end

function Sync.pushLane()
	local list = {}
	for _, entry in ipairs(lane) do
		table.insert(list, {
			id = entry.id,
			name = entry.spec.name,
			rarity = entry.spec.rarity,
			rate = entry.rate,
			cost = entry.spec.cost,
			mutation = entry.mutation,
		})
	end
	Remotes.LaneUpdate:FireAllClients(list)
end

function Sync.pushSlots(player)
	local d = playerData[player]
	if not d then
		return
	end
	local slots = {}
	for slot, entry in pairs(d.owned) do
		slots[slot] = {
			name = entry.spec.name,
			rarity = entry.spec.rarity,
			rate = entry.rate,
			mutation = entry.mutation,
		}
	end
	local locked = d.lockUntil > os.clock()
	Remotes.SlotsUpdate:FireClient(player, slots, locked, math.max(0, math.floor(d.lockUntil - os.clock())))
end

function Sync.pushCarry(player)
	local d = playerData[player]
	if not d then
		return
	end
	if d.carrying then
		Remotes.CarryUpdate:FireClient(player, d.carrying.spec.name, d.carrying.rate)
	else
		Remotes.CarryUpdate:FireClient(player, "", 0)
	end
end

-- Quests + prize book: quest states (progress, target, reward, claimed)
-- and the collection (how many of the 36 characters this player has ever
-- docked, and which ones) for the HUD's quests panel and prize book.
function Sync.pushQuests(player)
	local d = playerData[player]
	if not d then
		return
	end
	local states = {}
	for _, q in ipairs(QUESTS) do
		table.insert(states, {
			id = q.id,
			name = q.name,
			target = q.target,
			reward = q.reward,
			progress = math.min(questProgress(d, q.id), q.target),
			claimed = d.quests.claimed[q.id] == true,
		})
	end
	local foundCount = 0
	local foundIds = {}
	for id in pairs(d.found) do
		foundCount += 1
		table.insert(foundIds, id)
	end
	Remotes.QuestsUpdate:FireClient(player, states, foundCount, foundIds)
end

-- ---------------------------------------------------------------- Store
local Store = {}

function Store.load(player)
	local data = {
		money = E.startMoney,
		rebirths = 0,
		found = {},
		quests = { bought = 0, stolen = 0, waves = 0, claimed = {} },
	}
	if store then
		local ok, saved = pcall(function()
			return store:GetAsync("player_" .. player.UserId)
		end)
		if ok and type(saved) == "table" then
			if type(saved.money) == "number" then
				data.money = saved.money
			end
			if type(saved.rebirths) == "number" then
				data.rebirths = saved.rebirths
			end
			if type(saved.found) == "table" then
				data.found = saved.found
			end
			if type(saved.quests) == "table" then
				local q = saved.quests
				data.quests = {
					bought = q.bought or 0,
					stolen = q.stolen or 0,
					waves = q.waves or 0,
					claimed = q.claimed or {},
				}
			end
		end
	end
	return data
end

function Store.save(player)
	local d = playerData[player]
	if not d or not store then
		return
	end
	pcall(function()
		store:SetAsync("player_" .. player.UserId, {
			money = math.floor(d.money),
			rebirths = d.rebirths,
			found = d.found,
			quests = d.quests,
		})
	end)
end

-- ---------------------------------------------------------------- Conveyor
local Conveyor = {}

function Conveyor.find(id)
	for i, entry in ipairs(lane) do
		if entry.id == id then
			return entry, i
		end
	end
	return nil, nil
end

function Conveyor.spawn(spec, mutation)
	if #lane >= E.maxOnLane then
		return nil
	end
	spec = spec or BrainrotData.rollCharacter()
	mutation = mutation or BrainrotData.rollMutation()
	laneSeq += 1
	local model = CharacterFactory.build(spec, mutation.name)
	model.Name = "Lane_" .. tostring(laneSeq)
	model:PivotTo(CFrame.new(E.laneFromX, 0.5, 0))
	model.Parent = workspace
	local entry = {
		id = laneSeq,
		model = model,
		spec = spec,
		mutation = mutation.name,
		rate = CharacterFactory.effectiveRate(spec, mutation.name),
		x = E.laneFromX,
	}
	table.insert(lane, entry)
	-- Click the 3D brainrot on the lane to buy it.
	local click = model.PrimaryPart:FindFirstChildOfClass("ClickDetector")
	if click then
		click.MouseClick:Connect(function(player)
			tryBuy(player, entry.id)
		end)
	end
	Sync.pushLane()
	return entry
end

-- ---------------------------------------------------------------- buy / carry / dock
-- tryBuy and trySteal are globals on purpose: the conveyor's click
-- detectors (wired in Conveyor.spawn, before these are defined) and the
-- docked models' detectors resolve them when a player actually clicks.
function tryBuy(player, laneId)
	local d = playerData[player]
	if not d then
		return
	end
	if d.carrying then
		notify(player, "Hands full! Dock your brainrot at your base first.", "warn")
		return
	end
	local entry, idx = Conveyor.find(laneId)
	if not entry then
		return
	end
	local root = Util.rootPart(player)
	if not root or Util.distance(root.Position, entry.model:GetPivot().Position) > 45 then
		notify(player, "Walk up to the conveyor to buy it!", "warn")
		return
	end
	if d.money < entry.spec.cost then
		notify(player, "Not enough cash! Need " .. FormatUtil.money(entry.spec.cost) .. ".", "warn")
		return
	end
	d.money -= entry.spec.cost
	table.remove(lane, idx)
	d.carrying = {
		spec = entry.spec,
		mutation = entry.mutation,
		rate = entry.rate,
		model = entry.model,
	}
	d.quests.bought += 1
	entry.model:SetAttribute("Owner", player.Name)
	notify(player, "Bought " .. entry.spec.name .. "! Carry it home to your base.", "success")
	Sync.pushMoney(player)
	Sync.pushLane()
	Sync.pushCarry(player)
	Sync.pushQuests(player)
end

local function freeSlot(d)
	for slot = 1, E.baseSlots do
		if not d.owned[slot] then
			return slot
		end
	end
	return nil
end

local function dockCarried(player)
	local d = playerData[player]
	if not d or not d.carrying or not d.baseIndex then
		return
	end
	local slot = freeSlot(d)
	if not slot then
		notify(player, "Your base is full! Sell or rebirth to make room.", "warn")
		return
	end
	local base = Bases.model(d.baseIndex)
	if not base then
		return
	end
	local pad = base:FindFirstChild("Slot" .. tostring(slot))
	if not pad then
		return
	end
	local entry = d.carrying
	d.carrying = nil
	d.owned[slot] = entry
	-- The prize book remembers every character this player has ever docked.
	d.found[entry.spec.id] = true
	local padPos = pad.Position
	entry.model:PivotTo(CFrame.new(padPos.X, padPos.Y + 3.4, padPos.Z))
	entry.model:SetAttribute("Slot", slot)
	entry.model:SetAttribute("Owner", player.Name)
	-- Click a docked brainrot to steal it (if its base is unlocked).
	local click = entry.model.PrimaryPart:FindFirstChildOfClass("ClickDetector")
	if click then
		click.MouseClick:Connect(function(thief)
			trySteal(thief, player, slot)
		end)
	end
	notify(player, "Docked " .. entry.spec.name .. "! +" .. FormatUtil.rate(entry.rate) .. " forever.", "success")
	Sync.pushMoney(player)
	Sync.pushSlots(player)
	Sync.pushCarry(player)
	Sync.pushQuests(player)
end

-- ---------------------------------------------------------------- stealing & locks
function trySteal(thief, victim, slot)
	local vd = playerData[victim]
	local td = playerData[thief]
	if not vd or not td or thief == victim then
		return
	end
	local entry = vd.owned[slot]
	if not entry then
		return
	end
	if td.carrying then
		notify(thief, "Hands full! Dock your brainrot first.", "warn")
		return
	end
	if vd.lockUntil > os.clock() then
		notify(thief, "That base is LOCKED. Come back later!", "warn")
		return
	end
	local thiefRoot = Util.rootPart(thief)
	if not thiefRoot or Util.distance(thiefRoot.Position, entry.model:GetPivot().Position) > 30 then
		notify(thief, "Get closer to steal it!", "warn")
		return
	end
	notify(thief, "Stealing " .. entry.spec.name .. "... 3s. Don't get caught!", "warn")
	notify(victim, "SOMEONE IS STEALING YOUR " .. string.upper(entry.spec.name) .. "! RUN HOME!", "danger")
	task.wait(E.stealTime)
	-- Re-check everything: the steal only lands if the base is still
	-- unlocked and the owner did not make it home in time.
	if vd.owned[slot] ~= entry then
		return
	end
	if vd.lockUntil > os.clock() then
		notify(thief, "Too slow — they locked the base!", "warn")
		return
	end
	local victimRoot = Util.rootPart(victim)
	if victimRoot and thiefRoot and Util.distance(victimRoot.Position, thiefRoot.Position) < 20 then
		notify(thief, "CAUGHT! The owner came home!", "danger")
		notify(victim, "You caught the thief! Your " .. entry.spec.name .. " is safe.", "success")
		return
	end
	vd.owned[slot] = nil
	td.carrying = {
		spec = entry.spec,
		mutation = entry.mutation,
		rate = entry.rate,
		model = entry.model,
	}
	td.quests.stolen += 1
	entry.model:SetAttribute("Owner", thief.Name)
	entry.model:SetAttribute("Slot", 0)
	notify(thief, "STOLE " .. entry.spec.name .. "! Run it to YOUR base!", "success")
	notify(victim, "Your " .. entry.spec.name .. " was stolen!", "danger")
	Sync.pushSlots(victim)
	Sync.pushCarry(thief)
	Sync.pushMoney(victim)
	Sync.pushQuests(thief)
end

-- ---------------------------------------------------------------- remotes
local function bindRemotes()
	Remotes.LockBase.OnServerEvent:Connect(function(player)
		local d = playerData[player]
		if not d or not d.baseIndex then
			return
		end
		if d.lockUntil > os.clock() then
			notify(player, "Base already locked.", "warn")
			return
		end
		if d.lockCooldownUntil > os.clock() then
			notify(player, "Lock recharging: " .. FormatUtil.clock(d.lockCooldownUntil - os.clock()) .. " left.", "warn")
			return
		end
		if d.money < E.lockCost then
			notify(player, "Lock costs " .. FormatUtil.money(E.lockCost) .. ".", "warn")
			return
		end
		d.money -= E.lockCost
		d.lockUntil = os.clock() + E.lockDuration
		d.lockCooldownUntil = os.clock() + E.lockDuration + E.lockCooldown
		Bases.setLockBeam(d.baseIndex, true)
		notify(player, "Base LOCKED for " .. E.lockDuration .. "s. Nobody can steal from you.", "success")
		Sync.pushMoney(player)
		Sync.pushSlots(player)
		task.delay(E.lockDuration, function()
			if playerData[player] then
				Bases.setLockBeam(d.baseIndex, false)
				Sync.pushSlots(player)
			end
		end)
	end)

	Remotes.RebirthRequest.OnServerEvent:Connect(function(player)
		local d = playerData[player]
		if not d then
			return
		end
		local hasMythic = false
		for _, entry in pairs(d.owned) do
			if entry.spec.rarity == "Mythic" or entry.spec.rarity == "Secret"
				or entry.spec.rarity == "Divine" then
				hasMythic = true
				break
			end
		end
		if not hasMythic then
			notify(player, "Rebirth needs a Mythic (or better) brainrot on your base.", "warn")
			return
		end
		if d.money < E.rebirthCost then
			notify(player, "Rebirth costs " .. FormatUtil.money(E.rebirthCost) .. ".", "warn")
			return
		end
		for _, entry in pairs(d.owned) do
			if entry.model then
				entry.model:Destroy()
			end
		end
		d.owned = {}
		d.money = E.startMoney
		d.rebirths += 1
		notify(player, "REBIRTH x" .. tostring(d.rebirths) .. "! Income is now x" .. tostring(1 + d.rebirths * E.rebirthMult) .. " forever.", "success")
		Sync.pushMoney(player)
		Sync.pushSlots(player)
	end)

	Remotes.BuyBrainrot.OnServerEvent:Connect(function(player, laneId)
		tryBuy(player, laneId)
	end)

	-- Quest claims: the server checks completion and pays exactly once.
	Remotes.ClaimQuest.OnServerEvent:Connect(function(player, questId)
		local d = playerData[player]
		if not d then
			return
		end
		local def = nil
		for _, q in ipairs(QUESTS) do
			if q.id == questId then
				def = q
				break
			end
		end
		if not def then
			return
		end
		if d.quests.claimed[questId] then
			notify(player, "Quest already claimed.", "warn")
			return
		end
		if questProgress(d, questId) < def.target then
			notify(player, "Quest not finished yet.", "warn")
			return
		end
		d.quests.claimed[questId] = true
		d.money += def.reward
		notify(player, "Quest complete! +" .. FormatUtil.money(def.reward) .. " — " .. def.name, "success")
		Sync.pushMoney(player)
		Sync.pushQuests(player)
	end)

	Remotes.StealBrainrot.OnServerEvent:Connect(function(player, victimUserId, slot)
		local victim = Players:GetPlayerByUserId(victimUserId)
		if victim then
			trySteal(player, victim, slot)
		end
	end)
end

-- ---------------------------------------------------------------- wave
local function runWave()
	Remotes.WaveEvent:FireAllClients("warning", E.waveWarn)
	task.wait(E.waveWarn)
	local wall = Instance.new("Part")
	wall.Name = "TsunamiWall"
	wall.Anchored = true
	wall.CanCollide = false
	wall.Size = Vector3.new(320, 26, 4)
	wall.Color = Color3.fromRGB(40, 120, 255)
	wall.Material = Enum.Material.Neon
	wall.Transparency = 0.35
	wall.CFrame = CFrame.new(0, 13, -170)
	wall.Parent = workspace
	local tween = TweenService:Create(wall, TweenInfo.new(8, Enum.EasingStyle.Linear), {
		CFrame = CFrame.new(0, 13, 170),
	})
	tween:Play()
	Remotes.WaveEvent:FireAllClients("hit", 8)
	task.wait(4) -- the wall crosses the middle of the map: resolve the catch
	for player, d in pairs(playerData) do
		if d.carrying and not inOwnBase(player) then
			local c = d.carrying
			d.carrying = nil
			Conveyor.spawn(c.spec, { name = c.mutation, mult = 1 })
			if c.model then
				c.model:Destroy()
			end
			notify(player, "The wave swept away your " .. c.spec.name .. "! It washed back to the conveyor.", "danger")
			Sync.pushCarry(player)
		end
	end
	-- Survived the wave: everyone who was safe inside their own base when
	-- the wall passed gets the quest tick.
	for player, d in pairs(playerData) do
		if inOwnBase(player) then
			d.quests.waves += 1
			Sync.pushQuests(player)
		end
	end
	tween.Completed:Wait()
	wall:Destroy()
	Remotes.WaveEvent:FireAllClients("clear")
end

-- ---------------------------------------------------------------- players
local function bindPlayers()
	Players.PlayerAdded:Connect(function(player)
		local ls = Instance.new("Folder")
		ls.Name = "leaderstats"
		ls.Parent = player
		local moneyValue = Instance.new("IntValue")
		moneyValue.Name = "Money"
		moneyValue.Parent = ls
		local rebirthValue = Instance.new("IntValue")
		rebirthValue.Name = "Rebirths"
		rebirthValue.Parent = ls

		local saved = Store.load(player)
		local baseIndex = nil
		for i = 1, 8 do
			if not baseOwner[i] then
				baseOwner[i] = player
				baseIndex = i
				break
			end
		end
		playerData[player] = {
			money = saved.money,
			rebirths = saved.rebirths,
			baseIndex = baseIndex,
			owned = {},
			carrying = nil,
			lockUntil = 0,
			lockCooldownUntil = 0,
			found = saved.found,
			quests = saved.quests,
		}
		if baseIndex then
			Bases.sign(baseIndex, player.Name .. "'s BASE")
			notify(player, "Welcome to Brainrot Bay! Your base is #" .. tostring(baseIndex) .. ". Buy a brainrot from the conveyor!", "success")
		else
			notify(player, "All 8 bases are taken — you are spectating this round.", "warn")
		end
		Sync.pushMoney(player)
		Sync.pushLane()
		Sync.pushSlots(player)
		Sync.pushCarry(player)
		Sync.pushQuests(player)
	end)

	Players.PlayerRemoving:Connect(function(player)
		local d = playerData[player]
		if not d then
			return
		end
		Store.save(player)
		if d.baseIndex then
			baseOwner[d.baseIndex] = nil
			Bases.sign(d.baseIndex, "BASE " .. tostring(d.baseIndex))
			Bases.setLockBeam(d.baseIndex, false)
		end
		for _, entry in pairs(d.owned) do
			if entry.model then
				entry.model:Destroy()
			end
		end
		if d.carrying and d.carrying.model then
			d.carrying.model:Destroy()
		end
		playerData[player] = nil
	end)
end

bindRemotes()
bindPlayers()

-- ---------------------------------------------------------------- loops
task.spawn(function()
	while true do
		task.wait(1)
		for player, d in pairs(playerData) do
			local gain = incomePerSecond(d)
			if gain > 0 then
				d.money += gain
			end
			Sync.pushMoney(player)
		end
	end
end)

task.spawn(function()
	while true do
		task.wait(E.spawnInterval)
		Conveyor.spawn()
	end
end)

-- Conveyor movement + carrying follow + auto-dock, every frame.
game:GetService("RunService").Heartbeat:Connect(function(dt)
	waveClock += dt
	for _, entry in ipairs(lane) do
		entry.x += E.laneSpeed * dt
		if entry.x > E.laneToX then
			entry.model:Destroy()
		else
			local bob = 0.5 + math.sin(waveClock * 3 + entry.id) * 0.15
			entry.model:PivotTo(CFrame.new(entry.x, bob, 0))
		end
	end
	-- Sweep despawned lane entries.
	for i = #lane, 1, -1 do
		if lane[i].x > E.laneToX then
			table.remove(lane, i)
		end
	end
	-- Carried brainrots float above their owner's head; docking is automatic
	-- the moment the owner steps onto their own base.
	for player, d in pairs(playerData) do
		if d.carrying then
			local root = Util.rootPart(player)
			if root then
				local bob = 4.6 + math.sin(waveClock * 4) * 0.25
				d.carrying.model:PivotTo(CFrame.new(root.Position.X, root.Position.Y + bob, root.Position.Z))
				if inOwnBase(player) then
					dockCarried(player)
				end
			end
		end
	end
end)

task.spawn(function()
	while true do
		task.wait(60)
		for player in pairs(playerData) do
			Store.save(player)
		end
	end
end)

task.spawn(function()
	while true do
		task.wait(E.waveInterval)
		runWave()
	end
end)

print("Brainrot Bay server ready: 8 bases, conveyor, stealing, locks, rebirths, tsunami, 36 characters, 7 rarities, 6 mutations, quests + prize book.")
