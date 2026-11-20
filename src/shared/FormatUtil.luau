-- Small formatting helpers shared by server and client.
-- One job: turn numbers into readable money, rates and timers.
-- Every function is pure: same input, same string out, every time.

local FormatUtil = {}

-- Big-number suffixes, largest first. The format is part of the entry so
-- the branch below is one loop instead of three near-identical ifs.
--   1,234,567,890 -> "$1.23B" ; 1,234,567 -> "$1.23M" ; 12,345 -> "$12.3K"
local SUFFIXES = {
	{ threshold = 1e9, divisor = 1e9, format = "$%.2fB" },
	{ threshold = 1e6, divisor = 1e6, format = "$%.2fM" },
	{ threshold = 1e4, divisor = 1e3, format = "$%.1fK" },
}

-- 1234 -> "$1,234". Groups of three from the right, via reverse so the
-- pattern only has to match a plain run of digits.
local function commas(n)
	local s = tostring(n)
	local grouped = string.reverse(s)
	grouped = string.gsub(grouped, "(%d%d%d)", "%1,")
	grouped = string.reverse(grouped)
	grouped = string.gsub(grouped, "^,", "")
	return "$" .. grouped
end

-- 1234 -> "$1,234" ; 1234567 -> "$1.23M" ; 1234567890 -> "$1.23B"
function FormatUtil.money(n)
	n = math.floor(n + 0.5)
	for _, suf in ipairs(SUFFIXES) do
		if n >= suf.threshold then
			return string.format(suf.format, n / suf.divisor)
		end
	end
	return commas(n)
end

function FormatUtil.rate(n)
	return FormatUtil.money(n) .. "/s"
end

-- 95 -> "1:35"
function FormatUtil.clock(seconds)
	seconds = math.max(0, math.floor(seconds + 0.5))
	local minutes = math.floor(seconds / 60)
	local rest = seconds % 60
	return string.format("%d:%02d", minutes, rest)
end

return FormatUtil
