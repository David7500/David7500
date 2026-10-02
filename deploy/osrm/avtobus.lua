-- Avtobus za OSRM: avtomobilski profil, ki sme tudi tja, kamor sme samo
-- javni prevoz.
--
-- Rabimo ga samo za pripenjanje tras GTFS na ceste OSM (`kajros/pripni.py`),
-- ne za iskanje poti. Avtomobilski profil sam bi avtobus speljal okrog
-- cest, zaprtih za avtomobile (Slovenska cesta v Ljubljani, avtobusni
-- pasovi, dovozi na avtobusne postaje), in trasa bi zavila drugam, kot
-- avtobus vozi.
package.path = '/opt/?.lua;' .. package.path
local avto = dofile('/opt/car.lua')

local function setup()
  local p = avto.setup()

  -- `bus=yes`, `psv=designated` ... pred splošnimi oznakami dostopa.
  p.access_tags_hierarchy = Sequence { 'bus', 'psv', 'motor_vehicle', 'vehicle', 'access' }
  for _, k in ipairs({ 'psv', 'bus', 'minibus' }) do
    p.access_tag_whitelist[k] = true
    p.access_tag_blacklist[k] = nil
  end
  -- Prepovedi zavijanja z `except=psv` za avtobus ne veljajo, enosmernost
  -- z `oneway:bus=no` prav tako ne.
  p.restrictions = Sequence { 'bus', 'psv', 'motor_vehicle', 'vehicle' }

  p.speeds.highway.busway = 40
  p.speeds.highway.bus_guideway = 40
  p.restricted_highway_whitelist.busway = true
  return p
end

return {
  setup = setup,
  process_way = avto.process_way,
  process_node = avto.process_node,
  process_turn = avto.process_turn,
}
