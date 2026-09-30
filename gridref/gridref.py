"""Draw a map-reference grid around the board, so a position can be named.

Finding a spot on a board by millimetre coordinates means reading the cursor
readout and hunting. A lettered and numbered grid turns that into "the island
is on E9", which is one glance. The grid is drawn on a user layer, so it never
reaches the fabricator, and it is collected in a named group so the same button
can remove it again without touching anything else on that layer.

Columns carry numbers and run left to right, rows carry letters and run top to
bottom, which is the convention on street maps and the one most people already
read without being told.
"""

import json
import os

import pcbnew
import wx

MM = 1000000.0
GROUP_NAME = "GridRef"
# Settings belong in the user's own configuration, never in the plugin folder:
# that folder is a git checkout, and a file written there shows up as a change
# to the repository every time the dialog is used.
SETTINGS_DIR = os.path.join(os.path.expanduser("~"), ".config", "kicad-plugins")
SETTINGS_PATH = os.path.join(SETTINGS_DIR, "gridref.json")

DEFAULTS = {
    "cell_mm": 2.5,
    "layer": "Cmts.User",
    "text_mm": 0.6,
    "text_stroke_mm": 0.08,
    "line_mm": 0.10,
    "frame_mm": 0.15,
    "draw_lines": True,
    "labels_top": True,
    "labels_bottom": True,
    "labels_left": True,
    "labels_right": True,
    "margin_mm": 1.3,
}

# Layers a grid may be drawn on. Every one of them is excluded from a normal
# fabrication output, which is the point: the grid is a reading aid, not artwork.
LAYER_CHOICES = ["Cmts.User", "Dwgs.User", "Eco1.User", "Eco2.User",
                 "User.1", "User.2", "User.3", "User.4"]


def load_settings():
    """Settings live beside the plugin, so they follow it into every project."""
    values = dict(DEFAULTS)
    try:
        with open(SETTINGS_PATH) as handle:
            values.update(json.load(handle))
    except Exception:
        pass
    return values


def save_settings(values):
    try:
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        with open(SETTINGS_PATH, "w") as handle:
            json.dump(values, handle, indent=1)
    except Exception:
        pass


def column_label(index):
    """1, 2, 3 ... for the horizontal axis."""
    return str(index + 1)


def row_label(index):
    """A, B ... Z, AA, AB ... for the vertical axis, so a tall board keeps working."""
    label = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        label = chr(ord("A") + remainder) + label
    return label


def find_group(board):
    for group in board.Groups():
        if group.GetName() == GROUP_NAME:
            return group
    return None


def remove_grid(board):
    """Remove only what this plugin drew, by way of its group."""
    group = find_group(board)
    if group is None:
        return 0
    removed = 0
    for item in list(group.GetItems()):
        board.Remove(item)
        removed += 1
    board.Remove(group)
    return removed


def draw_grid(board, cfg):
    box = board.GetBoardEdgesBoundingBox()
    if box.GetWidth() <= 0 or box.GetHeight() <= 0:
        raise ValueError("Das Board hat keinen Umriss auf Edge.Cuts.")

    layer = board.GetLayerID(cfg["layer"])
    if layer < 0:
        raise ValueError("Die Lage %s gibt es auf diesem Board nicht." % cfg["layer"])

    x0, y0 = box.GetLeft() / MM, box.GetTop() / MM
    x1, y1 = box.GetRight() / MM, box.GetBottom() / MM
    cell = float(cfg["cell_mm"])
    columns = max(1, int(round((x1 - x0) / cell)))
    rows = max(1, int(round((y1 - y0) / cell)))

    group = pcbnew.PCB_GROUP(board)
    group.SetName(GROUP_NAME)
    board.Add(group)

    def point(x, y):
        return pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))

    def line(ax, ay, bx, by, width):
        shape = pcbnew.PCB_SHAPE(board)
        shape.SetShape(pcbnew.SHAPE_T_SEGMENT)
        shape.SetLayer(layer)
        shape.SetStart(point(ax, ay))
        shape.SetEnd(point(bx, by))
        shape.SetWidth(int(round(width * MM)))
        board.Add(shape)
        group.AddItem(shape)

    def label(value, x, y):
        text = pcbnew.PCB_TEXT(board)
        text.SetText(value)
        text.SetLayer(layer)
        text.SetPosition(point(x, y))
        size = int(round(float(cfg["text_mm"]) * MM))
        text.SetTextSize(pcbnew.VECTOR2I(size, size))
        text.SetTextThickness(int(round(float(cfg["text_stroke_mm"]) * MM)))
        text.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
        text.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        board.Add(text)
        group.AddItem(text)

    frame = float(cfg["frame_mm"])
    line(x0, y0, x1, y0, frame)
    line(x0, y1, x1, y1, frame)
    line(x0, y0, x0, y1, frame)
    line(x1, y0, x1, y1, frame)

    margin = float(cfg["margin_mm"])
    inner = float(cfg["line_mm"])

    for index in range(columns + 1):
        x = x0 + index * cell
        if cfg["draw_lines"] and 0 < index < columns:
            line(x, y0, x, y1, inner)
        if index < columns:
            middle = x + cell / 2.0
            if cfg["labels_top"]:
                label(column_label(index), middle, y0 - margin)
            if cfg["labels_bottom"]:
                label(column_label(index), middle, y1 + margin)

    for index in range(rows + 1):
        y = y0 + index * cell
        if cfg["draw_lines"] and 0 < index < rows:
            line(x0, y, x1, y, inner)
        if index < rows:
            middle = y + cell / 2.0
            if cfg["labels_left"]:
                label(row_label(index), x0 - margin, middle)
            if cfg["labels_right"]:
                label(row_label(index), x1 + margin, middle)

    return columns, rows


class GridRefDialog(wx.Dialog):
    """One panel for every value the grid has, plus the two actions."""

    def __init__(self, parent, cfg, has_grid):
        wx.Dialog.__init__(self, parent, title="Planquadrat-Raster",
                           style=wx.DEFAULT_DIALOG_STYLE)
        self.cfg = dict(cfg)
        outer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.FlexGridSizer(0, 2, 6, 10)
        grid.AddGrowableCol(1, 1)

        def row(caption, control):
            grid.Add(wx.StaticText(self, label=caption), 0,
                     wx.ALIGN_CENTER_VERTICAL)
            grid.Add(control, 1, wx.EXPAND)
            return control

        def number(key, low, high, step):
            spin = wx.SpinCtrlDouble(self, min=low, max=high, inc=step,
                                     value=str(cfg[key]))
            spin.SetDigits(2)
            return spin

        self.cell = row("Rastermass in mm", number("cell_mm", 0.5, 25.0, 0.5))
        self.layer = row("Lage", wx.Choice(self, choices=LAYER_CHOICES))
        self.layer.SetSelection(
            LAYER_CHOICES.index(cfg["layer"]) if cfg["layer"] in LAYER_CHOICES else 0)
        self.text = row("Schrifthöhe in mm", number("text_mm", 0.2, 5.0, 0.1))
        self.stroke = row("Strichstärke Schrift", number("text_stroke_mm", 0.02, 1.0, 0.01))
        self.line = row("Strichstärke Raster", number("line_mm", 0.02, 1.0, 0.01))
        self.frame = row("Strichstärke Rahmen", number("frame_mm", 0.02, 1.0, 0.01))
        self.margin = row("Abstand der Beschriftung", number("margin_mm", 0.2, 10.0, 0.1))

        outer.Add(grid, 0, wx.ALL | wx.EXPAND, 12)

        self.lines = wx.CheckBox(self, label="Rasterlinien zeichnen")
        self.lines.SetValue(bool(cfg["draw_lines"]))
        outer.Add(self.lines, 0, wx.LEFT | wx.RIGHT, 12)

        sides = wx.StaticBoxSizer(wx.StaticBox(self, label="Beschriftung an"),
                                  wx.HORIZONTAL)
        self.top = wx.CheckBox(self, label="oben")
        self.bottom = wx.CheckBox(self, label="unten")
        self.left = wx.CheckBox(self, label="links")
        self.right = wx.CheckBox(self, label="rechts")
        for box, key in ((self.top, "labels_top"), (self.bottom, "labels_bottom"),
                         (self.left, "labels_left"), (self.right, "labels_right")):
            box.SetValue(bool(cfg[key]))
            sides.Add(box, 0, wx.ALL, 6)
        outer.Add(sides, 0, wx.ALL | wx.EXPAND, 12)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.remove = wx.Button(self, wx.ID_DELETE, "Raster entfernen")
        self.remove.Enable(has_grid)
        buttons.Add(self.remove, 0, wx.RIGHT, 8)
        buttons.AddStretchSpacer(1)
        buttons.Add(wx.Button(self, wx.ID_CANCEL, "Abbrechen"), 0, wx.RIGHT, 8)
        buttons.Add(wx.Button(self, wx.ID_OK, "Zeichnen"), 0)
        outer.Add(buttons, 0, wx.ALL | wx.EXPAND, 12)

        self.SetSizerAndFit(outer)
        self.remove.Bind(wx.EVT_BUTTON, lambda event: self.EndModal(wx.ID_DELETE))

    def values(self):
        return {
            "cell_mm": self.cell.GetValue(),
            "layer": LAYER_CHOICES[self.layer.GetSelection()],
            "text_mm": self.text.GetValue(),
            "text_stroke_mm": self.stroke.GetValue(),
            "line_mm": self.line.GetValue(),
            "frame_mm": self.frame.GetValue(),
            "margin_mm": self.margin.GetValue(),
            "draw_lines": self.lines.GetValue(),
            "labels_top": self.top.GetValue(),
            "labels_bottom": self.bottom.GetValue(),
            "labels_left": self.left.GetValue(),
            "labels_right": self.right.GetValue(),
        }


class GridRefPlugin(pcbnew.ActionPlugin):

    def defaults(self):
        self.name = "Planquadrat-Raster"
        self.category = "Modify PCB"
        self.description = ("Zeichnet ein beschriftetes Raster um das Board, "
                            "damit sich Stellen benennen lassen")
        self.show_toolbar_button = True
        # Two icons, because one set of colours cannot serve both toolbars: dark
        # lines vanish on a dark toolbar and light ones vanish on a light one.
        here = os.path.dirname(os.path.abspath(__file__))
        self.icon_file_name = os.path.join(here, "icon.png")
        self.dark_icon_file_name = os.path.join(here, "icon_dark.png")

    def Run(self):
        board = pcbnew.GetBoard()
        cfg = load_settings()
        dialog = GridRefDialog(None, cfg, find_group(board) is not None)
        try:
            answer = dialog.ShowModal()
            if answer == wx.ID_CANCEL:
                return
            if answer == wx.ID_DELETE:
                removed = remove_grid(board)
                pcbnew.Refresh()
                wx.MessageBox("%d Objekte entfernt." % removed, "Planquadrat-Raster")
                return
            cfg = dialog.values()
        finally:
            dialog.Destroy()

        save_settings(cfg)
        # Redrawing replaces rather than stacks, so the button can be pressed
        # twice with a different cell size without leaving the first grid behind.
        remove_grid(board)
        try:
            columns, rows = draw_grid(board, cfg)
        except ValueError as error:
            wx.MessageBox(str(error), "Planquadrat-Raster", wx.ICON_ERROR)
            return
        pcbnew.Refresh()
        wx.MessageBox("Raster gezeichnet: %d Spalten (1 bis %s), %d Zeilen (A bis %s)."
                      % (columns, column_label(columns - 1), rows, row_label(rows - 1)),
                      "Planquadrat-Raster")


GridRefPlugin().register()
