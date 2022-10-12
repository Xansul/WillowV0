import WillowConfig as WC
import requests
import json
import re
import webcolors

#LIGHTS
#dictionary of light entities
light_entities = {
    r"[bB]edroom": "light.bedroom_zha_group_0x0007",
    r"[kK]itchen\s*[cC]olor": "light.kitchen_back_zha_group_0x0003",
    r"[kK]itchen\s*([mM]ain)*": "light.kitchen_front_zha_group_0x0004",
    r"[lL]iving\s*([rR]oom)*": "light.living_room_zha_group_0x0012",
    r"[mM]antle": "light.mantle_color_zha_group_0x0002",
    r"[oO]ffice": "light.office_zha_group_0x0008",
    r"[mM]ain\s*([rR]oom)*": "light.main_room_zha_group_0x000f"
}
#match given light name to entity id
def FindEntity(text):
    for name in light_entities:
        if re.search(name, text):
            return light_entities[name]

#does color exist in CSS3
def DoesColorExist(text):
    no_spaces_text = re.sub(r"\s", "", text)
    for color in webcolors.css3_names_to_hex:
        if re.search(color, no_spaces_text):
            return True

#find color name
def FindColorName(text):
    no_spaces_text = re.sub(r"\s", "", text)
    for color in webcolors.css3_names_to_hex:
        if re.search(color, no_spaces_text):
            return color

#find temp type
def FindTempType(text):
    if re.search(r"low", text):
        return 160
    if re.search(r"high", text):
        return 400

#toggle lights function
def ToggleLights(entity):
    payload = {"entity_id": entity}

    payload = json.dumps(payload)

    response = requests.post(WC.endpoint_toggle, headers=WC.headers, data=payload)
    print(response.text)

#change light color function
def ChangeLightColor(entity, color):

    color_rgb = webcolors.name_to_rgb(color)

    payload = {"entity_id": entity, "rgb_color": color_rgb}

    payload = json.dumps(payload)

    response = requests.post(WC.endpoint_power, headers=WC.headers, data=payload)
    print(response.text)

def ChangeLightTemp(entity, temp):

    payload = {"entity_id": entity, "color_temp": temp}
    
    payload = json.dumps(payload)

    response = requests.post(WC.endpoint_power, headers=WC.headers, data=payload)
    print(response.text)