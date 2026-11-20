-- Builds a brainrot character model from a BrainrotData spec.
-- One job: spec in, Model out. The model is built only from Roblox parts
-- (no meshes, no decals), so it renders identically in Studio and in the
-- headless renders made from the same spec.
--
-- Every character gets a BillboardGui with a readable name line and a
-- rarity-coloured "$/s" line, plus a ClickDetector the server wires up
-- (buy on the conveyor, steal on a base).

local CharacterFactory = {}

local BrainrotData = require(script.Parent.BrainrotData)

local function makePart(spec)
	local p = Instance.new("Part")
	p.Anchored = true
	p.CanCollide = false
	p.Color = spec.color
	p.Material = spec.material or Enum.Material.SmoothPlastic
	if spec.shape == "Ball" then
		p.Shape = Enum.PartType.Ball
		p.Size = spec.size
		p.CFrame = CFrame.new(spec.offset)
	elseif spec.shape == "Cylinder" then
		p.Shape = Enum.PartType.Cylinder
		-- Roblox cylinders run along X; the spec stores (diameter, height).
		p.Size = Vector3.new(spec.height, spec.diameter, spec.diameter)
		p.CFrame = CFrame.new(spec.offset) * CFrame.Angles(0, 0, math.rad(90))
	else
		p.Shape = Enum.PartType.Block
		p.Size = spec.size
		p.CFrame = CFrame.new(spec.offset)
	end
	return p
end

function CharacterFactory.effectiveRate(spec, mutationName)
	local mult = 1
	for _, m in ipairs(BrainrotData.MUTATIONS) do
		if m.name == mutationName then
			mult = m.mult
			break
		end
	end
	return spec.rate * mult
end

function CharacterFactory.rarityColor(rarityName)
	local r = BrainrotData.RARITIES[rarityName]
	if r then
		return r.color
	end
	return Color3.fromRGB(255, 255, 255)
end

-- spec: a BrainrotData.CHARACTERS entry. mutationName: "None" | "Golden" | "Diamond" | "Rainbow".
function CharacterFactory.build(spec, mutationName)
	mutationName = mutationName or "None"
	local model = Instance.new("Model")
	model.Name = spec.name

	local body = nil
	for _, partSpec in ipairs(spec.parts) do
		local p = makePart(partSpec)
		p.Name = "Part"
		p.Parent = model
		if body == nil then
			body = p
		end
	end
	model.PrimaryPart = body

	-- Mutation ring: a glowing halo that makes the variant readable at a glance.
	if mutationName ~= "None" then
		local ringColor = nil
		for _, m in ipairs(BrainrotData.MUTATIONS) do
			if m.name == mutationName then
				ringColor = m.color
				break
			end
		end
		if ringColor then
			local ring = Instance.new("Part")
			ring.Name = "MutationRing"
			ring.Anchored = true
			ring.CanCollide = false
			ring.Shape = Enum.PartType.Cylinder
			ring.Size = Vector3.new(0.3, 5.8, 5.8)
			ring.CFrame = CFrame.new(0, 1.2, 0) * CFrame.Angles(0, 0, math.rad(90))
			ring.Color = ringColor
			ring.Material = Enum.Material.Neon
			ring.Transparency = 0.25
			ring.Parent = model
		end
	end

	-- Readable label: name on top, rarity + $/s below, coloured by rarity.
	-- Height follows the model's own top so the label floats above the head
	-- (models were scaled up in round 2; a fixed offset would clip tall ones).
	local top = 0
	for _, partSpec in ipairs(spec.parts) do
		local h = 0
		if partSpec.shape == "Cylinder" then
			h = partSpec.height / 2
		else
			h = partSpec.size.Y / 2
		end
		top = math.max(top, partSpec.offset.Y + h)
	end
	local rate = CharacterFactory.effectiveRate(spec, mutationName)
	local gui = Instance.new("BillboardGui")
	gui.Name = "Label"
	gui.Size = UDim2.fromOffset(160, 64)
	gui.StudsOffset = Vector3.new(0, top + 1.2, 0)
	gui.AlwaysOnTop = false
	gui.Parent = model

	local nameLabel = Instance.new("TextLabel")
	nameLabel.Name = "Name"
	nameLabel.Size = UDim2.new(1, 0, 0.55, 0)
	nameLabel.BackgroundTransparency = 1
	nameLabel.Font = Enum.Font.FredokaOne
	nameLabel.TextSize = 20
	nameLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
	nameLabel.TextStrokeTransparency = 0.4
	nameLabel.Text = spec.name
	nameLabel.Parent = gui

	local rateText = string.upper(spec.rarity) .. "  •  $" .. tostring(rate) .. "/s"
	if mutationName ~= "None" then
		rateText = string.upper(mutationName) .. " " .. rateText
	end
	local rateLabel = Instance.new("TextLabel")
	rateLabel.Name = "Rate"
	rateLabel.Position = UDim2.new(0, 0, 0.55, 0)
	rateLabel.Size = UDim2.new(1, 0, 0.45, 0)
	rateLabel.BackgroundTransparency = 1
	rateLabel.Font = Enum.Font.GothamBold
	rateLabel.TextSize = 16
	rateLabel.TextColor3 = CharacterFactory.rarityColor(spec.rarity)
	rateLabel.TextStrokeTransparency = 0.4
	rateLabel.Text = rateText
	rateLabel.Parent = gui

	local click = Instance.new("ClickDetector")
	click.Name = "Click"
	click.MaxActivationDistance = 64
	click.Parent = body

	model:SetAttribute("CharacterId", spec.id)
	model:SetAttribute("Rate", rate)
	model:SetAttribute("Cost", spec.cost)
	model:SetAttribute("Rarity", spec.rarity)
	model:SetAttribute("Mutation", mutationName)
	return model
end

return CharacterFactory
