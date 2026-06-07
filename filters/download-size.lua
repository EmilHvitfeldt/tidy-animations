-- Appends the on-disk file size to download links (.gif / .mp4 / .zip).
-- Sizes are resolved at render time, so they stay accurate after a re-capture
-- and need no server Content-Length header.

local function filesize(path)
  local f = io.open(path, "rb")
  if not f then return nil end
  local size = f:seek("end")
  f:close()
  return size
end

local function human(bytes)
  if bytes < 1024 then
    return string.format("%d B", bytes)
  elseif bytes < 1024 * 1024 then
    return string.format("%d KB", math.floor(bytes / 1024 + 0.5))
  else
    return string.format("%.1f MB", bytes / (1024 * 1024))
  end
end

function Link(el)
  local target = el.target
  if not (target:match("%.gif$") or target:match("%.mp4$") or target:match("%.zip$")) then
    return nil
  end

  local size = filesize(target)
  if not size then return nil end

  local label = pandoc.Span(" (" .. human(size) .. ")")
  label.classes = { "size" }
  table.insert(el.content, label)
  return el
end
