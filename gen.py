#!/usr/bin/env python3

import sys, os
from svgwrite import Drawing
from random import randint

# To convert SVG into printable PDF
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF, renderPM


def generate(d, rows, cols, adj_scale, previous=[]):
    dpi = 96
    scale = adj_scale * dpi/25.4
    fillet_rad = 2.5*scale
    circle_rad = 1.25*scale
    circle_grid = 5.08*scale
    rect_w = 43.*scale
    rect_h = 12.7*scale

    border = 2.25*scale
    xoff = rect_w/2 + border + 2.75*scale
    yoff = rect_h/2 + border + 2.75*scale
    required = 1 | (1<<7) | (1<<8) | (1<<15)

    vals = []
    while len(vals) < (rows*cols):
        rand = randint(0, 65536)
        rand |= required
        top = bin(rand)[3:9]
        bottom = bin(rand)[11:17]

        # require at least one dot per row
        if top == '000000' or top == '111111':
            continue

        # require 10 total dots
        if bin(rand).count('1') != 10:
            continue

        # discard if dots are in a rotationally-symmetric pattern
        if top == ''.join(reversed(bottom)):
            continue

        top180 = ''.join(reversed(bottom))
        bottom180 = ''.join(reversed(top))
        rand180 = ((int(bottom180, 2) << 1) + (int(top180, 2) << 9)) | required

        # check if an exact duplicate exists
        if not ( rand in vals \
              or rand in previous \
              or rand180 in vals \
              or rand180 in previous):
            vals.append(rand)

    row_col = []
    for r in range(rows):
        for c in range(cols):
            row_col.append((r,c))
    gen = zip(row_col, vals)

    for (r, c), spots in gen:
        xoff2 = xoff + c*(rect_w + border)
        yoff2 = yoff + r*(rect_h + border)

        # draw rounded rectangle
        cmds = [
            'M {} {}'.format(-rect_w/2 + fillet_rad + xoff2, rect_h/2 + yoff2),
            'A{},{} 0 0,1 {},{}'.format(fillet_rad, fillet_rad, -rect_w/2 + xoff2, rect_h/2 - fillet_rad + yoff2),
            'L {} {}'.format(-rect_w/2 + xoff2, -rect_h/2 + fillet_rad + yoff2),
            'A{},{} 0 0,1 {},{}'.format(fillet_rad, fillet_rad, -rect_w/2 + fillet_rad + xoff2, -rect_h/2 + yoff2),
            'L {} {}'.format(rect_w/2 - fillet_rad + xoff2, -rect_h/2 + yoff2),
            'A{},{} 0 0,1 {},{}'.format(fillet_rad, fillet_rad, rect_w/2 + xoff2, -rect_h/2 + fillet_rad + yoff2),
            'L {} {}'.format(rect_w/2 + xoff2, rect_h/2 - fillet_rad + yoff2),
            'A{},{} 0 0,1 {},{}'.format(fillet_rad, fillet_rad, rect_w/2 - fillet_rad + xoff2, rect_h/2 + yoff2),
            'z'
            ]

        d.add(d.path(d=''.join(cmds), fill='black', stroke='none'))

        for i in range(8):
            if spots & (1<<i):
                d.add(d.circle(center=((-3.5 + i)*circle_grid + xoff2, circle_grid/2 + yoff2), r=circle_rad, fill='white'))
            if spots & (1<<(i+8)):
                d.add(d.circle(center=((-3.5 + i)*circle_grid + xoff2, -circle_grid/2 + yoff2), r=circle_rad, fill='white'))
    return vals

def generate_multiple(rows, cols, adj_scale, num_files, path):
    out = []
    previous = []

    for i in range(num_files):
        dwg = Drawing(filename=os.path.join(path, '{}.svg'.format(i)), debug=True)
        previous.extend(generate(dwg, rows, cols, adj_scale, previous))
        #dwg.save()
        out.append(dwg.tostring())
    return out


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print('usage: {} <rows> <columns> <number of files> <adjust_scale> <output_path>'.format(sys.argv[0]))
        raise SystemExit

    rows = int(sys.argv[1])
    cols = int(sys.argv[2])
    num_files = int(sys.argv[3])
    adj_scale = float(sys.argv[4])
    path = sys.argv[5]

    max_count = 451 # total number of valid fiducials (based on exhaustive search)

    if rows*cols*num_files > max_count:
        print('error, only {} fiducials exist; requested {}'.format(max_count, rows*cols*num_files))
        raise SystemExit

    previous = []

    for i in range(num_files):
        svgfile = os.path.join(path,'dominoes-{}.svg'.format(i))
        dwg = Drawing(filename=svgfile)
        previous.extend(generate(dwg, rows, cols, adj_scale, previous))
        dwg.save()

        rpldwg = svg2rlg(svgfile)
        renderPDF.drawToFile(rpldwg, svgfile.replace('.svg','.pdf'))
