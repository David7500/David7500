-- Vlak za OSRM: samo tiri, brez ostrih zavojev.
--
-- Rabimo ga samo za pripenjanje tras SŽ na tire OSM (`kajros/pripni.py`).
-- Trase GTFS so od tira v mediani 2,2 m, ponekod pa več kot 25 m (skupaj
-- 28 km, največ v Kopru in Mariboru).
api_version = 4
package.path = '/opt/?.lua;' .. package.path

Set = require('lib/set')
Sequence = require('lib/sequence')

-- Tovorni tiri in industrijski priključki: potniški vlak tam ne vozi, ob
-- postaji pa jih je veliko in pripenjanje bi traso sicer lahko speljalo
-- čeznje. Stranski tiri (`siding`) ostanejo -- ob peronih so pogosto taki.
local NE_SERVICE = Set { 'yard', 'spur' }
local NE_USAGE = Set { 'industrial', 'military', 'test' }

function setup()
  return {
    properties = {
      max_speed_for_map_matching = 200 / 3.6,
      weight_name = 'duration',
      process_call_tagless_node = false,
      u_turn_penalty = 1000,
      continue_straight_at_waypoint = true,
      use_turn_restrictions = false,
      left_hand_driving = false,
    },
    default_mode = mode.train,
    default_speed = 80,
  }
end

function process_node(profile, node, result, relations)
end

function process_way(profile, way, result, relations)
  local railway = way:get_value_by_key('railway')
  if railway ~= 'rail' then
    return
  end
  if NE_SERVICE[way:get_value_by_key('service') or ''] or NE_USAGE[way:get_value_by_key('usage') or ''] then
    return
  end
  local hitrost = 80
  local service = way:get_value_by_key('service')
  if service then
    hitrost = 40
  end
  local maxspeed = tonumber(way:get_value_by_key('maxspeed') or '')
  if maxspeed and maxspeed > 0 then
    hitrost = math.min(maxspeed, 160)
  end
  result.forward_mode = mode.train
  result.backward_mode = mode.train
  result.forward_speed = hitrost
  result.backward_speed = hitrost
  result.name = way:get_value_by_key('name') or ''
end

function process_turn(profile, turn)
  -- Kretnica dovoli le majhen kot. Brez kazni bi pripenjanje na postaji
  -- obrnilo čez kretnico ali zavilo pravokotno, česar vlak ne more.
  turn.duration = 0
  if math.abs(turn.angle) > 40 or turn.is_u_turn then
    -- 1 000 s: kazen se hrani v desetinkah sekunde kot 16-bitno število,
    -- 3 600 s je preseglo obseg (`positive_overflow` ob gradnji).
    turn.duration = 1000
  end
  turn.weight = turn.duration
end

return {
  setup = setup,
  process_way = process_way,
  process_node = process_node,
  process_turn = process_turn,
}
