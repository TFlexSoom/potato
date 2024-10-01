"""
module: annotation
filename: color.py
date: 09/26/2024
author: David Jurgens and Jiaxin Pei (aka Pedro)
desc: Helper file for annotation in getting the colors for
  the project question
"""

COLOR_PALETTE = [
    "rgb(179,226,205)",
    "rgb(253,205,172)",
    "rgb(203,213,232)",
    "rgb(244,202,228)",
    "rgb(230,245,201)",
    "rgb(255,242,174)",
    "rgb(241,226,204)",
    "rgb(204,204,204)",
    "rgb(102, 197, 204)",
    "rgb(246, 207, 113)",
    "rgb(248, 156, 116)",
    "rgb(220, 176, 242)",
    "rgb(135, 197, 95)",
    "rgb(158, 185, 243)",
    "rgb(254, 136, 177)",
    "rgb(201, 219, 116)",
    "rgb(139, 224, 164)",
    "rgb(180, 151, 231)",
    "rgb(179, 179, 179)",
]

def get_color_for_schema_label(schema, label):
    global schema_label_to_color

    t = (schema, label)
    if t in schema_label_to_color:
        return schema_label_to_color[t]
    c = COLOR_PALETTE[len(schema_label_to_color)]
    schema_label_to_color[t] = c
    return c