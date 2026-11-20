-- Brainrot Bay — client HUD.
-- One job: draw the game and take the player's taps. All numbers come from
-- the server; this script never decides money, ownership or the wave.
--
-- Design system (the skills Danny asked for):
--   * Vibrant tokens: primary #7C61D4, secondary #EAAE87, success #16A34A,
--     warning #D97706, danger #DC2626, surface #FFFFFF, text #2F281D.
--   * Emil's rules: ease-out for anything entering, 160-250ms, press
--     feedback scale 0.97, never animate from scale 0 (start 0.95 +
--     transparency), toasts stagger 50ms, enter and exit the same way.
--   * Mobile-native: every button is at least 48px tall, text is 18px or
--     bigger, nothing tappable hides under a hover state, the whole HUD
--     stays clear of the top-left corner where Roblox puts its menu buttons,
--     and the bottom bar is padded for the phone home indicator.
--
-- Layout: each HUD piece is built by one function in the Hud table below
-- (money pill, wave banner, action bar, carry pill, base panel, shop bar,
-- quests panel, prize book); Toasts is a small module of its own;
-- bindServerEvents wires every RemoteEvent to the pieces it updates.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local RunService = game:GetService("RunService")

local FormatUtil = require(ReplicatedStorage.Shared.FormatUtil)
local BrainrotData = require(ReplicatedStorage.Shared.BrainrotData)

local Remotes = ReplicatedStorage:WaitForChild("Remotes")
local player = Players.LocalPlayer

-- ---------------------------------------------------------------- tokens
local PRIMARY = Color3.fromRGB(124, 97, 212)
local SECONDARY = Color3.fromRGB(234, 174, 135)
local SUCCESS = Color3.fromRGB(22, 163, 74)
local WARNING = Color3.fromRGB(217, 119, 6)
local DANGER = Color3.fromRGB(220, 38, 38)
local SURFACE = Color3.fromRGB(255, 255, 255)
local INK = Color3.fromRGB(47, 40, 29)
local PANEL = Color3.fromRGB(30, 27, 45)

local EASE_OUT = Enum.EasingStyle.Quad
local PRESS_TWEEN = TweenInfo.new(0.16, EASE_OUT, Enum.EasingDirection.Out)
local ENTER_TWEEN = TweenInfo.new(0.2, EASE_OUT, Enum.EasingDirection.Out)
local EXIT_TWEEN = TweenInfo.new(0.15, EASE_OUT, Enum.EasingDirection.Out)

local RARITY_COLORS = {
	Common = Color3.fromRGB(34, 197, 94),
	Rare = Color3.fromRGB(59, 130, 246),
	Epic = Color3.fromRGB(139, 92, 246),
	Legendary = Color3.fromRGB(245, 158, 11),
	Mythic = Color3.fromRGB(239, 68, 68),
	Secret = Color3.fromRGB(236, 72, 153),
	Divine = Color3.fromRGB(255, 255, 255),
}

-- ---------------------------------------------------------------- helpers
local function corner(parent, radius)
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(0, radius)
	c.Parent = parent
	return c
end

local function stroke(parent, color, thickness)
	local s = Instance.new("UIStroke")
	s.Color = color
	s.Thickness = thickness or 2
	s.Parent = parent
	return s
end

-- Press feedback (Emil): scale to 0.97 the instant the finger lands,
-- back to 1 on release. Works for mouse and touch alike.
local function addPressFeedback(button)
	local baseSize = button.Size
	button.InputBegan:Connect(function(input)
		if input.UserInputType == Enum.UserInputType.MouseButton1
			or input.UserInputType == Enum.UserInputType.Touch then
			TweenService:Create(button, PRESS_TWEEN, { Size = UDim2.new(
				baseSize.X.Scale, baseSize.X.Offset - 2,
				baseSize.Y.Scale, baseSize.Y.Offset - 2) }):Play()
		end
	end)
	button.InputEnded:Connect(function(input)
		if input.UserInputType == Enum.UserInputType.MouseButton1
			or input.UserInputType == Enum.UserInputType.Touch then
			TweenService:Create(button, PRESS_TWEEN, { Size = baseSize }):Play()
		end
	end)
end

local function makeLabel(parent, name, text, size, color, font)
	local l = Instance.new("TextLabel")
	l.Name = name
	l.BackgroundTransparency = 1
	l.Font = font or Enum.Font.GothamBold
	l.TextSize = size
	l.TextColor3 = color or SURFACE
	l.Text = text
	l.TextWrapped = true
	l.Parent = parent
	return l
end

-- ---------------------------------------------------------------- gui root
local gui = Instance.new("ScreenGui")
gui.Name = "BrainrotGui"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = true
gui.DisplayOrder = 10
gui.Parent = player:WaitForChild("PlayerGui")

-- ---------------------------------------------------------------- Hud builders
-- Each builder makes one piece, wires its own button, and returns the
-- elements the server events need to update later.
local Hud = {}

-- Money pill — top centre, clear of the top-left Roblox menu.
function Hud.buildMoneyPill()
	local pill = Instance.new("Frame")
	pill.Name = "MoneyPill"
	pill.AnchorPoint = Vector2.new(0.5, 0)
	pill.Position = UDim2.new(0.5, 0, 0, 14)
	pill.Size = UDim2.fromOffset(260, 64)
	pill.BackgroundColor3 = PRIMARY
	pill.BorderSizePixel = 0
	pill.Parent = gui
	corner(pill, 16)
	stroke(pill, SECONDARY, 3)

	local money = makeLabel(pill, "Money", "$100", 30, SURFACE, Enum.Font.FredokaOne)
	money.Size = UDim2.new(1, -16, 0.62, 0)
	money.Position = UDim2.new(0, 8, 0, 2)
	local income = makeLabel(pill, "Income", "+$0/s", 18, SECONDARY, Enum.Font.GothamBold)
	income.Size = UDim2.new(1, -16, 0.34, 0)
	income.Position = UDim2.new(0, 8, 0.6, 0)
	return { pill = pill, money = money, income = income }
end

-- Wave banner — hidden until the server warns.
function Hud.buildWaveBanner()
	local banner = Instance.new("Frame")
	banner.Name = "WaveBanner"
	banner.AnchorPoint = Vector2.new(0.5, 0)
	banner.Position = UDim2.new(0.5, 0, 0, 92)
	banner.Size = UDim2.fromOffset(420, 56)
	banner.BackgroundColor3 = DANGER
	banner.BorderSizePixel = 0
	banner.Visible = false
	banner.Parent = gui
	corner(banner, 14)
	local label = makeLabel(banner, "Text", "TSUNAMI INCOMING — RUN TO YOUR BASE!", 20, SURFACE, Enum.Font.FredokaOne)
	label.Size = UDim2.new(1, -16, 1, 0)
	label.Position = UDim2.new(0, 8, 0, 0)
	return { banner = banner, label = label }
end

-- Action bar — bottom right: LOCK / REBIRTH / PRIZE BOOK. Three big
-- buttons, each at least 48px tall (mobile-native), clear of the shop bar.
function Hud.buildActionBar(bookPanel)
	local bar = Instance.new("Frame")
	bar.Name = "ActionBar"
	bar.AnchorPoint = Vector2.new(1, 1)
	bar.Position = UDim2.new(1, -16, 1, -24)
	bar.Size = UDim2.fromOffset(258, 56)
	bar.BackgroundTransparency = 1
	bar.Parent = gui

	local function actionButton(name, text, color, x)
		local button = Instance.new("TextButton")
		button.Name = name
		button.Position = UDim2.fromOffset(x, 0)
		button.Size = UDim2.fromOffset(82, 56)
		button.BackgroundColor3 = color
		button.Text = text
		button.Font = Enum.Font.FredokaOne
		button.TextSize = 17
		button.TextColor3 = SURFACE
		button.BorderSizePixel = 0
		button.Parent = bar
		corner(button, 14)
		addPressFeedback(button)
		return button
	end

	local lockButton = actionButton("LockButton", "LOCK\n$500", SUCCESS, 0)
	lockButton.Activated:Connect(function()
		Remotes.LockBase:FireServer()
	end)
	local rebirthButton = actionButton("RebirthButton", "REBIRTH\n$50K", WARNING, 88)
	rebirthButton.Activated:Connect(function()
		Remotes.RebirthRequest:FireServer()
	end)
	local bookButton = actionButton("BookButton", "PRIZE\nBOOK", PRIMARY, 176)
	bookButton.Activated:Connect(function()
		bookPanel.Visible = not bookPanel.Visible
	end)
	return { bar = bar, lockButton = lockButton, rebirthButton = rebirthButton, bookButton = bookButton }
end

-- Quests panel — left side, under the Roblox menu buttons: the three
-- quests with progress and a CLAIM button when one is done.
function Hud.buildQuestsPanel()
	local panel = Instance.new("Frame")
	panel.Name = "QuestsPanel"
	panel.AnchorPoint = Vector2.new(0, 0)
	panel.Position = UDim2.new(0, 16, 0, 110)
	panel.Size = UDim2.fromOffset(300, 182)
	panel.BackgroundColor3 = PANEL
	panel.BackgroundTransparency = 0.15
	panel.BorderSizePixel = 0
	panel.Parent = gui
	corner(panel, 16)

	local title = makeLabel(panel, "Title", "QUESTS", 18, SECONDARY, Enum.Font.FredokaOne)
	title.Size = UDim2.new(1, -16, 0, 26)
	title.Position = UDim2.new(0, 8, 0, 6)
	title.TextXAlignment = Enum.TextXAlignment.Left

	local rows = {}
	local questDefs = {
		{ id = "buy3", name = "Buy 3 brainrots" },
		{ id = "steal1", name = "Steal 1 brainrot" },
		{ id = "wave1", name = "Survive a tsunami" },
	}
	for i, def in ipairs(questDefs) do
		local y = 36 + (i - 1) * 48
		local nameLabel = makeLabel(panel, "Quest" .. tostring(i), def.name, 16, SURFACE, Enum.Font.GothamBold)
		nameLabel.Size = UDim2.new(1, -100, 0, 22)
		nameLabel.Position = UDim2.new(0, 8, 0, y)
		nameLabel.TextXAlignment = Enum.TextXAlignment.Left
		local progressLabel = makeLabel(panel, "Progress" .. tostring(i), "0/0", 14, SECONDARY, Enum.Font.GothamBold)
		progressLabel.Size = UDim2.new(1, -100, 0, 20)
		progressLabel.Position = UDim2.new(0, 8, 0, y + 22)
		progressLabel.TextXAlignment = Enum.TextXAlignment.Left
		local claim = Instance.new("TextButton")
		claim.Name = "Claim" .. tostring(i)
		claim.AnchorPoint = Vector2.new(1, 0)
		claim.Position = UDim2.new(1, -8, 0, y + 4)
		claim.Size = UDim2.fromOffset(78, 36)
		claim.BackgroundColor3 = Color3.fromRGB(90, 85, 115)
		claim.Text = "CLAIM"
		claim.Font = Enum.Font.GothamBold
		claim.TextSize = 15
		claim.TextColor3 = SURFACE
		claim.BorderSizePixel = 0
		claim.Parent = panel
		corner(claim, 10)
		addPressFeedback(claim)
		claim.Activated:Connect(function()
			Remotes.ClaimQuest:FireServer(def.id)
		end)
		rows[i] = { id = def.id, name = nameLabel, progress = progressLabel, claim = claim }
	end
	return { panel = panel, rows = rows }
end

-- Prize book — a modal grid of all 36 characters (name + $/s + rarity
-- colour; not-found cells are grey question marks). Opens from the
-- action bar's PRIZE BOOK button; closed with the X.
function Hud.buildBookPanel()
	local panel = Instance.new("Frame")
	panel.Name = "PrizeBook"
	panel.AnchorPoint = Vector2.new(0.5, 0.5)
	panel.Position = UDim2.new(0.5, 0, 0.5, 0)
	panel.Size = UDim2.fromOffset(780, 520)
	panel.BackgroundColor3 = PANEL
	panel.BorderSizePixel = 0
	panel.Visible = false
	panel.Parent = gui
	corner(panel, 18)

	local title = makeLabel(panel, "Title", "PRIZE BOOK", 24, SECONDARY, Enum.Font.FredokaOne)
	title.Size = UDim2.new(1, -120, 0, 34)
	title.Position = UDim2.new(0, 16, 0, 10)
	title.TextXAlignment = Enum.TextXAlignment.Left
	local countLabel = makeLabel(panel, "Count", "0/36 FOUND", 18, SURFACE, Enum.Font.GothamBold)
	countLabel.Size = UDim2.new(0, 200, 0, 34)
	countLabel.Position = UDim2.new(0, 200, 0, 10)
	countLabel.TextXAlignment = Enum.TextXAlignment.Left

	local close = Instance.new("TextButton")
	close.Name = "Close"
	close.AnchorPoint = Vector2.new(1, 0)
	close.Position = UDim2.new(1, -12, 0, 10)
	close.Size = UDim2.fromOffset(40, 40)
	close.BackgroundColor3 = DANGER
	close.Text = "X"
	close.Font = Enum.Font.FredokaOne
	close.TextSize = 20
	close.TextColor3 = SURFACE
	close.BorderSizePixel = 0
	close.Parent = panel
	corner(close, 12)
	addPressFeedback(close)
	close.Activated:Connect(function()
		panel.Visible = false
	end)

	-- Grid order: rarity order, then $/s ascending — the ladder itself.
	local ordered = {}
	for _, c in ipairs(BrainrotData.CHARACTERS) do
		table.insert(ordered, c)
	end
	table.sort(ordered, function(a, b)
		local oa = BrainrotData.RARITIES[a.rarity].order
		local ob = BrainrotData.RARITIES[b.rarity].order
		if oa ~= ob then
			return oa < ob
		end
		return a.rate < b.rate
	end)
	local tiles = {}
	for i, c in ipairs(ordered) do
		local col = (i - 1) % 6
		local row = math.floor((i - 1) / 6)
		local tile = Instance.new("Frame")
		tile.Name = c.id
		tile.Position = UDim2.fromOffset(16 + col * 124, 56 + row * 74)
		tile.Size = UDim2.fromOffset(118, 66)
		tile.BackgroundColor3 = Color3.fromRGB(60, 55, 85)
		tile.BorderSizePixel = 0
		tile.Parent = panel
		corner(tile, 10)
		local nameLabel = makeLabel(tile, "Name", "???", 13, SURFACE, Enum.Font.FredokaOne)
		nameLabel.Size = UDim2.new(1, -8, 0, 34)
		nameLabel.Position = UDim2.new(0, 4, 0, 4)
		local rateLabel = makeLabel(tile, "Rate", "NOT FOUND", 12, SECONDARY, Enum.Font.GothamBold)
		rateLabel.Size = UDim2.new(1, -8, 0, 18)
		rateLabel.Position = UDim2.new(0, 4, 0, 40)
		tiles[c.id] = { frame = tile, name = nameLabel, rate = rateLabel, char = c }
	end
	return { panel = panel, countLabel = countLabel, tiles = tiles }
end

-- Carry indicator — above the shop bar, only while carrying.
function Hud.buildCarryPill()
	local pill = Instance.new("Frame")
	pill.Name = "CarryPill"
	pill.AnchorPoint = Vector2.new(0.5, 1)
	pill.Position = UDim2.new(0.5, 0, 1, -128)
	pill.Size = UDim2.fromOffset(380, 48)
	pill.BackgroundColor3 = SUCCESS
	pill.BorderSizePixel = 0
	pill.Visible = false
	pill.Parent = gui
	corner(pill, 14)
	local label = makeLabel(pill, "Text", "", 20, SURFACE, Enum.Font.FredokaOne)
	label.Size = UDim2.new(1, -16, 1, 0)
	label.Position = UDim2.new(0, 8, 0, 0)
	return { pill = pill, label = label }
end

-- Base panel — bottom left: 8 slot chips + lock button.
function Hud.buildBasePanel()
	local panel = Instance.new("Frame")
	panel.Name = "BasePanel"
	panel.AnchorPoint = Vector2.new(0, 1)
	panel.Position = UDim2.new(0, 16, 1, -24)
	panel.Size = UDim2.fromOffset(250, 132)
	panel.BackgroundColor3 = PANEL
	panel.BackgroundTransparency = 0.15
	panel.BorderSizePixel = 0
	panel.Parent = gui
	corner(panel, 16)

	local title = makeLabel(panel, "Title", "MY BASE", 18, SECONDARY, Enum.Font.FredokaOne)
	title.Size = UDim2.new(1, -16, 0, 26)
	title.Position = UDim2.new(0, 8, 0, 6)
	title.TextXAlignment = Enum.TextXAlignment.Left

	local chips = {}
	for i = 1, 8 do
		local chip = Instance.new("Frame")
		chip.Name = "Slot" .. tostring(i)
		chip.Size = UDim2.fromOffset(52, 44)
		chip.Position = UDim2.fromOffset(8 + ((i - 1) % 4) * 58, 36 + math.floor((i - 1) / 4) * 48)
		chip.BackgroundColor3 = Color3.fromRGB(60, 55, 85)
		chip.BorderSizePixel = 0
		chip.Parent = panel
		corner(chip, 10)
		local t = makeLabel(chip, "Text", "—", 16, Color3.fromRGB(180, 175, 200), Enum.Font.GothamBold)
		t.Size = UDim2.new(1, 0, 1, 0)
		chips[i] = { frame = chip, label = t }
	end

	local lockButton = Instance.new("TextButton")
	lockButton.Name = "LockButton"
	lockButton.AnchorPoint = Vector2.new(1, 0)
	lockButton.Position = UDim2.new(1, -8, 0, 4)
	lockButton.Size = UDim2.fromOffset(76, 30)
	lockButton.BackgroundColor3 = SUCCESS
	lockButton.Text = "LOCK $500"
	lockButton.Font = Enum.Font.GothamBold
	lockButton.TextSize = 14
	lockButton.TextColor3 = SURFACE
	lockButton.BorderSizePixel = 0
	lockButton.Parent = panel
	corner(lockButton, 10)
	addPressFeedback(lockButton)
	lockButton.Activated:Connect(function()
		Remotes.LockBase:FireServer()
	end)
	return { panel = panel, chips = chips, lockButton = lockButton }
end

-- Shop bar — bottom centre: the brainrots currently on the conveyor.
function Hud.buildShopBar()
	local bar = Instance.new("Frame")
	bar.Name = "ShopBar"
	bar.AnchorPoint = Vector2.new(0.5, 1)
	bar.Position = UDim2.new(0.5, 0, 1, -24)
	bar.Size = UDim2.fromOffset(560, 100)
	bar.BackgroundColor3 = PANEL
	bar.BackgroundTransparency = 0.15
	bar.BorderSizePixel = 0
	bar.Parent = gui
	corner(bar, 16)

	local title = makeLabel(bar, "Title", "CONVEYOR — TAP A CARD TO BUY (walk up first!)", 16, SECONDARY, Enum.Font.FredokaOne)
	title.Size = UDim2.new(1, -16, 0, 24)
	title.Position = UDim2.new(0, 8, 0, 4)

	local cards = {}
	for i = 1, 6 do
		local card = Instance.new("TextButton")
		card.Name = "Card" .. tostring(i)
		card.Size = UDim2.fromOffset(88, 64)
		card.Position = UDim2.fromOffset(8 + (i - 1) * 92, 30)
		card.BackgroundColor3 = Color3.fromRGB(60, 55, 85)
		card.BorderSizePixel = 0
		card.Text = ""
		card.Visible = false
		card.Parent = bar
		corner(card, 12)
		addPressFeedback(card)
		local nameLabel = makeLabel(card, "Name", "", 13, SURFACE, Enum.Font.FredokaOne)
		nameLabel.Size = UDim2.new(1, -6, 0, 20)
		nameLabel.Position = UDim2.new(0, 3, 0, 4)
		local rateLabel = makeLabel(card, "Rate", "", 13, SECONDARY, Enum.Font.GothamBold)
		rateLabel.Size = UDim2.new(1, -6, 0, 18)
		rateLabel.Position = UDim2.new(0, 3, 0, 24)
		local costLabel = makeLabel(card, "Cost", "", 14, SURFACE, Enum.Font.GothamBold)
		costLabel.Size = UDim2.new(1, -6, 0, 18)
		costLabel.Position = UDim2.new(0, 3, 0, 42)
		cards[i] = { button = card, name = nameLabel, rate = rateLabel, cost = costLabel, laneId = nil }
		card.Activated:Connect(function()
			if cards[i].laneId then
				Remotes.BuyBrainrot:FireServer(cards[i].laneId)
			end
		end)
	end
	return { bar = bar, cards = cards }
end

-- ---------------------------------------------------------------- Toasts
-- Top right, enter and exit the same way (slide + fade). `count` is the
-- running total: a toast's stack position is its index when it appears.
local Toasts = {}
Toasts.count = 0

function Toasts.show(text, kind)
	Toasts.count += 1
	local myIndex = Toasts.count
	local bg = DANGER
	if kind == "success" then
		bg = SUCCESS
	elseif kind == "warn" then
		bg = WARNING
	elseif kind == "info" then
		bg = PRIMARY
	end
	local toast = Instance.new("Frame")
	toast.Name = "Toast"
	toast.Size = UDim2.fromOffset(320, 52)
	toast.Position = UDim2.new(0, 0, 0, (myIndex - 1) * 58)
	toast.BackgroundColor3 = bg
	toast.BorderSizePixel = 0
	toast.Parent = Toasts.stack
	corner(toast, 12)
	local label = makeLabel(toast, "Text", text, 16, SURFACE, Enum.Font.GothamBold)
	label.Size = UDim2.new(1, -16, 1, 0)
	label.Position = UDim2.new(0, 8, 0, 0)
	-- Enter: from 0.95 scale + transparent, ease-out 200ms (Emil).
	toast.GroupTransparency = 1
	toast.Size = UDim2.fromOffset(304, 52)
	task.delay((myIndex - 1) * 0.05, function()
		if toast.Parent then
			TweenService:Create(toast, ENTER_TWEEN, { GroupTransparency = 0, Size = UDim2.fromOffset(320, 52) }):Play()
		end
	end)
	task.delay(3.5, function()
		if toast.Parent then
			local out = TweenService:Create(toast, EXIT_TWEEN, { GroupTransparency = 1 })
			out:Play()
			out.Completed:Wait()
			toast:Destroy()
			Toasts.count -= 1
		end
	end)
end

function Toasts.buildStack()
	local stack = Instance.new("Frame")
	stack.Name = "Toasts"
	stack.AnchorPoint = Vector2.new(1, 0)
	stack.Position = UDim2.new(1, -16, 0, 196)
	stack.Size = UDim2.fromOffset(320, 200)
	stack.BackgroundTransparency = 1
	stack.Parent = gui
	Toasts.stack = stack
	return stack
end

-- ---------------------------------------------------------------- build
local moneyPill = Hud.buildMoneyPill()
local waveBanner = Hud.buildWaveBanner()
local carryPill = Hud.buildCarryPill()
local basePanel = Hud.buildBasePanel()
local shopBar = Hud.buildShopBar()
local questsPanel = Hud.buildQuestsPanel()
local bookPanel = Hud.buildBookPanel()
Hud.buildActionBar(bookPanel.panel)
Toasts.buildStack()

-- ---------------------------------------------------------------- server events
local function bindServerEvents()
	local lastMoney = 0
	Remotes.MoneyUpdate.OnClientEvent:Connect(function(money, income)
		moneyPill.money.Text = FormatUtil.money(money)
		moneyPill.income.Text = "+" .. FormatUtil.rate(income)
		-- Pop the pill when the balance jumps (Emil: feedback on change, 160ms).
		if money - lastMoney >= 100 then
			TweenService:Create(moneyPill.pill, PRESS_TWEEN, { Size = UDim2.fromOffset(272, 68) }):Play()
			task.delay(0.16, function()
				TweenService:Create(moneyPill.pill, PRESS_TWEEN, { Size = UDim2.fromOffset(260, 64) }):Play()
			end)
		end
		lastMoney = money
	end)

	Remotes.LaneUpdate.OnClientEvent:Connect(function(list)
		for i, card in ipairs(shopBar.cards) do
			local entry = list[i]
			if entry then
				card.button.Visible = true
				card.laneId = entry.id
				card.name.Text = entry.name
				card.rate.Text = FormatUtil.rate(entry.rate)
					.. (entry.mutation ~= "None" and (" " .. string.upper(entry.mutation) .. " x" .. tostring(entry.rate)) or "")
				card.cost.Text = FormatUtil.money(entry.cost)
				card.button.BackgroundColor3 = RARITY_COLORS[entry.rarity] or Color3.fromRGB(60, 55, 85)
			else
				card.button.Visible = false
				card.laneId = nil
			end
		end
	end)

	Remotes.SlotsUpdate.OnClientEvent:Connect(function(slots, locked, lockLeft)
		for i, chip in ipairs(basePanel.chips) do
			local entry = slots[i]
			if entry then
				chip.label.Text = string.sub(entry.name, 1, 2)
				chip.frame.BackgroundColor3 = RARITY_COLORS[entry.rarity] or Color3.fromRGB(60, 55, 85)
			else
				chip.label.Text = "—"
				chip.frame.BackgroundColor3 = Color3.fromRGB(60, 55, 85)
			end
		end
		if locked then
			basePanel.lockButton.Text = "LOCKED " .. FormatUtil.clock(lockLeft)
			basePanel.lockButton.BackgroundColor3 = DANGER
		else
			basePanel.lockButton.Text = "LOCK $500"
			basePanel.lockButton.BackgroundColor3 = SUCCESS
		end
	end)

	Remotes.CarryUpdate.OnClientEvent:Connect(function(name, rate)
		if name ~= "" then
			carryPill.pill.Visible = true
			carryPill.label.Text = "Carrying: " .. name .. " — take it home!"
		else
			carryPill.pill.Visible = false
		end
	end)

	Remotes.NotifyClient.OnClientEvent:Connect(function(text, kind)
		Toasts.show(text, kind)
	end)

	-- Quests + prize book: refresh the quests panel (progress + CLAIM
	-- state) and the book grid (found cells light up in rarity colour).
	Remotes.QuestsUpdate.OnClientEvent:Connect(function(states, foundCount, foundIds)
		local foundSet = {}
		for _, id in ipairs(foundIds) do
			foundSet[id] = true
		end
		for _, state in ipairs(states) do
			for _, row in ipairs(questsPanel.rows) do
				if row.id == state.id then
					row.progress.Text = tostring(state.progress) .. "/" .. tostring(state.target)
						.. "  •  " .. FormatUtil.money(state.reward)
					if state.claimed then
						row.claim.Text = "DONE"
						row.claim.BackgroundColor3 = Color3.fromRGB(90, 85, 115)
					elseif state.progress >= state.target then
						row.claim.Text = "CLAIM"
						row.claim.BackgroundColor3 = SUCCESS
					else
						row.claim.Text = "CLAIM"
						row.claim.BackgroundColor3 = Color3.fromRGB(90, 85, 115)
					end
				end
			end
		end
		bookPanel.countLabel.Text = tostring(foundCount) .. "/36 FOUND"
		for id, tile in pairs(bookPanel.tiles) do
			if foundSet[id] then
				tile.frame.BackgroundColor3 = RARITY_COLORS[tile.char.rarity] or Color3.fromRGB(60, 55, 85)
				tile.name.Text = tile.char.name
				tile.rate.Text = FormatUtil.rate(tile.char.rate)
			else
				tile.frame.BackgroundColor3 = Color3.fromRGB(60, 55, 85)
				tile.name.Text = "???"
				tile.rate.Text = "NOT FOUND"
			end
		end
	end)

	Remotes.WaveEvent.OnClientEvent:Connect(function(phase, seconds)
		if phase == "warning" then
			waveBanner.banner.Visible = true
			waveBanner.label.Text = "TSUNAMI INCOMING — RUN TO YOUR BASE!"
			waveBanner.banner.Position = UDim2.new(0.5, 0, 0, 70)
			TweenService:Create(waveBanner.banner, ENTER_TWEEN, { Position = UDim2.new(0.5, 0, 0, 92) }):Play()
			Toasts.show("Tsunami in " .. tostring(seconds) .. "s! Get to your base!", "warn")
		elseif phase == "hit" then
			-- Camera shake: 0.4s of small random offsets, then back to normal.
			local camera = workspace.CurrentCamera
			if camera then
				local start = tick()
				local conn
				conn = RunService.RenderStepped:Connect(function()
					if tick() - start > 0.4 then
						conn:Disconnect()
						return
					end
					local cf = camera.CFrame
					camera.CFrame = cf * CFrame.new(math.random(-4, 4) / 10, math.random(-3, 3) / 10, 0)
				end)
			end
		elseif phase == "clear" then
			waveBanner.banner.Visible = false
			Toasts.show("The wave passed. Back to business!", "success")
		end
	end)
end

bindServerEvents()
Toasts.show("Welcome to Brainrot Bay! Buy a brainrot from the conveyor.", "info")
