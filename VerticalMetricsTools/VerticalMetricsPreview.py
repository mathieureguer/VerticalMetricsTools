import drawBot as dt
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

import click

import pathlib

# ----------------------------------------

MARGIN = 20
HEADER = 100

# ----------------------------------------


class PseudoTable(dict):
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)


class PseudoFont(object):
    """
    A pseudo font object storing various vertical metrics info
    """
    os2_target_attr = [
        "sCapHeight",
        "sxHeight",

        "sTypoAscender",
        "sTypoDescender",
        "sTypoLineGap",

        "usWinAscent",
        "usWinDescent",

        "fsSelection"
    ]
    hhea_target_attr = [
        "ascent",
        "descent",
        "lineGap"
    ]
    head_target_attr = [
        "unitsPerEm"
    ]

    def __init__(self):
        self.os2 = PseudoTable()
        self.hhead = PseudoTable()

    def load_data_from_font(self, font):

        os2 = font.get("OS/2")
        os2_data = {a: getattr(os2, a) for a in self.os2_target_attr}
        self.os2 = PseudoTable(**os2_data)

        hhea = font.get("hhea")
        hhea_data = {a: getattr(hhea, a) for a in self.hhea_target_attr}
        self.hhea = PseudoTable(**hhea_data)

        head = font.get("head")
        head_data = {a: getattr(head, a) for a in self.head_target_attr}
        self.head = PseudoTable(**head_data)

        minimum, maximum = _find_vertical_min_max_glyph(font)
        self.min_glyph, self.min_y = minimum
        self.max_glyph, self.max_y = maximum

    @property
    def use_typo_metrics(self):
        fs_selection = _num_to_selected_bits(self.os2.fsSelection, bits=16)
        if 7 in fs_selection:
            return True
        else:
            return False
    


def _find_vertical_min_max_glyph(font):
    glyphs = font.getGlyphSet()
    ymins = {}
    ymaxs = {}
    for n in glyphs.keys():
        p = BoundsPen(font)
        glyphs[n].draw(p)
        bounds = p.bounds
        if bounds:
            xmin, ymin, xmax, ymax = bounds
            ymins[ymin] = n
            ymaxs[ymax] = n
    min_ = min(ymins.keys())
    max_ = max(ymaxs.keys())
    return ((ymins[min_], min_), (ymaxs[max_], max_))


def get_pseudo_font(font_path):
    font = TTFont(font_path)
    pseudo_font = PseudoFont()
    pseudo_font.load_data_from_font(font)
    return(pseudo_font)

def _num_to_selected_bits(num, bits=32):
    sel = []
    for i in range(bits):
        if num & 1 << i:
            sel.append(i)
    return sel


def _get_(num, description_map, default="None"):
    flags = _num_to_selected_bits(num, bits=16)
    if len(flags):
        string = ", ".join([description_map[b] for b in flags])
    else:
        string = default
    return string


# ----------------------------------------


def _line_with_caption(start_point,
                       end_point,
                       stroke,
                       caption,
                       stroke_width=1,
                       caption_font="Monaco",
                       caption_size=6):
    dt.save()
    dt.fill(*stroke)
    dt.stroke(*stroke)
    dt.strokeWidth(stroke_width)
    dt.line(start_point, end_point)

    dt.font(caption_font)
    dt.fontSize(caption_size)
    dt.stroke(None)
    dt.text(caption, (start_point[0], start_point[1] - caption_size * 1.2))

    dt.restore()


def _rect_with_caption(size,
                       color,
                       caption,
                       caption_font="Monaco",
                       caption_size=6):

    dt.save()
    dt.fill(*color)
    dt.stroke(None)
    x, y, w, h = size
    dt.rect(*size)
    dt.font(caption_font)
    dt.fontSize(caption_size)
    if h > 0:
        caption_inner = -caption_size * 1.5
    else:
        caption_inner = caption_size * .5

    dt.fill(0, 0, 0, .5)
    dt.text(caption, (x + caption_size * .5, y + h + caption_inner))
    dt.restore()


# ----------------------------------------
@click.command()
@click.option('-t', '--text', default="HÉdp", help='Specify a string to be rendered on the preview', type=str)
@click.option('-s', '--size', default=300, help='Specify the size of the preview string, in points', type=int)
@click.option('--extremum/--no-extremum', default=True, help='Add the vertical extremum glyphs to the preview string')
@click.argument("font_path", type=click.Path(exists=False))
def preview_vertical_metrics(font_path, text, size, extremum):
    font = dt.installFont(font_path)
    pseudo_font = get_pseudo_font(font_path)

    descenders = min(-pseudo_font.os2.usWinDescent,
                     pseudo_font.min_y,
                     pseudo_font.os2.sTypoDescender - pseudo_font.os2.sTypoLineGap / 2,
                     pseudo_font.hhea.descent - pseudo_font.hhea.lineGap / 2,
                     )
    ascenders = max(pseudo_font.os2.usWinAscent,
                    pseudo_font.max_y,
                    pseudo_font.os2.sTypoAscender + pseudo_font.os2.sTypoLineGap / 2,
                    pseudo_font.hhea.ascent + pseudo_font.hhea.lineGap / 2,
                    )
    upm_ratio = size / pseudo_font.head.unitsPerEm

    formatted_text = dt.FormattedString(font=font, fontSize=size, fill=0)
    formatted_text.append(text)
    if extremum:
        formatted_text.appendGlyph(pseudo_font.min_glyph, pseudo_font.max_glyph)
    _width, _ = dt.textSize(formatted_text)
    _width += MARGIN * 2 + HEADER
    _height = (ascenders - descenders) * upm_ratio + MARGIN * 2

    dt.newPage(_width, _height)
    dt.fill(1)
    dt.rect(0, 0, _width, _height)
    dt.font(font)
    dt.fontSize(size)
    dt.translate(0, -descenders * upm_ratio + MARGIN)

    origin_x = MARGIN
    metric_width = (_width - MARGIN * 2) / 3

    # ----------------------------------------
    # draw os2 metrics
    # no caption here, they will be added with the metrics guide later on

    _rect_with_caption((origin_x, 0, metric_width, pseudo_font.os2.sTypoAscender * upm_ratio),
                       (.5, 1, .5),
                       "")
    _rect_with_caption((origin_x, 0, metric_width, pseudo_font.os2.sTypoDescender * upm_ratio),
                       (0, 1, .3),
                       "")
    if pseudo_font.os2.sTypoLineGap > 0:
        # ascender_gap = pseudo_font.os2.usWinAscent - pseudo_font.os2.sTypoAscender
        # if pseudo_font.os2.sTypoLineGap > ascender_gap:
        #     line_gap_top = ascender_gap
        #     line_gap_bottom = pseudo_font.os2.sTypoLineGap - ascender_gap
        # else:
        #     line_gap_top = pseudo_font.os2.sTypoLineGap
        #     line_gap_bottom = 0
        _rect_with_caption((origin_x, pseudo_font.os2.sTypoAscender * upm_ratio, metric_width, pseudo_font.os2.sTypoLineGap * upm_ratio / 2),
                           (.8,),
                           f"sTypoLineGap: {pseudo_font.os2.sTypoLineGap}")
        _rect_with_caption((origin_x, pseudo_font.os2.sTypoDescender * upm_ratio, metric_width, -pseudo_font.os2.sTypoLineGap * upm_ratio / 2),
                           (.8,),
                           "")

    dt.fill(0)
    dt.font("Monaco")
    dt.fontSize(6)
    dt.text("OS/2 table", (origin_x, ascenders * upm_ratio + 4))
    dt.text(f"Use Typo Metrics: {pseudo_font.use_typo_metrics}", (origin_x, ascenders * upm_ratio - 20))
    origin_x += metric_width

    # ----------------------------------------
    # draw hhead metrics

    _rect_with_caption((origin_x, 0, metric_width, pseudo_font.hhea.ascent * upm_ratio),
                       (.5, 1, 1),
                       f"ascent: {pseudo_font.hhea.ascent}")

    _rect_with_caption((origin_x, 0, metric_width, pseudo_font.hhea.descent * upm_ratio),
                       (0, .5, 1),
                       f"descent: {pseudo_font.hhea.descent}")

    if pseudo_font.hhea.lineGap > 0:
        # ascender_gap = pseudo_font.hhea.ascent - pseudo_font.os2.sTypoAscender
        # if pseudo_font.hhea.lineGap > ascender_gap:
        #     line_gap_top = ascender_gap
        #     line_gap_bottom = pseudo_font.hhea.lineGap - ascender_gap
        # else:
        #     line_gap_top = pseudo_font.hhea.lineGap
        #     line_gap_bottom = 0

        _rect_with_caption((origin_x, pseudo_font.hhea.ascent * upm_ratio, metric_width, pseudo_font.hhea.lineGap * upm_ratio / 2),
                           (.8,),
                           f"lineGap: {pseudo_font.hhea.lineGap}")

        _rect_with_caption((origin_x, pseudo_font.hhea.descent * upm_ratio, metric_width, -pseudo_font.hhea.lineGap * upm_ratio / 2),
                           (.8,),
                           "")

    dt.fill(0)
    dt.font("Monaco")
    dt.fontSize(6)
    dt.text("Hhea table", (origin_x, ascenders * upm_ratio + 4))
    origin_x += metric_width

    # ----------------------------------------
    # draw usWin metrics

    _rect_with_caption((origin_x, 0, metric_width, pseudo_font.os2.usWinAscent * upm_ratio),
                       (1, .5, 1),
                       f"usWinAscent: {pseudo_font.os2.usWinAscent}")
    _rect_with_caption((origin_x, 0, metric_width, -pseudo_font.os2.usWinDescent * upm_ratio),
                       (1, 0, .5),
                       f"usWinDescent: {pseudo_font.os2.usWinDescent}")
    dt.fill(0)
    dt.font("Monaco")
    dt.fontSize(6)
    dt.text("Win table", (origin_x, ascenders * upm_ratio + 4))
    # origin_x += metric_width

    # ----------------------------------------
    # draw designer metrics

    line_start = MARGIN
    line_end = _width - MARGIN
    lines = ["baseline", "sxHeight", "sCapHeight", "sTypoAscender", "sTypoDescender"]
    for l in lines:
        y = pseudo_font.os2.get(l, 0)
        _line_with_caption((line_start, y * upm_ratio),
                           (line_end, y * upm_ratio),
                           (0, 0, 0, .5),
                           f"{l}: {y}",
                           stroke_width=.5)

    dt.fill(0)
    origin_x += metric_width

    # ----------------------------------------
    # and add the text

    dt.text(formatted_text, (MARGIN + HEADER, 0))

    # ----------------------------------------

    input_path = pathlib.PurePath(font_path)
    output_path = pathlib.Path.joinpath(input_path.parent, input_path.stem + '-verticalmetrics' + ".pdf")
    dt.saveImage(output_path)
    print(f"{output_path.name} saved.")
