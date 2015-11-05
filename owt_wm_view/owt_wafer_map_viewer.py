# -*- coding: utf-8 -*-
"""
@name:          owt_wafer_map_viewer.py
@created:       Mon Feb 23 14:55:23 2015

Usage:
    owt_wafer_map_viewer.py

Options:
    -h --help           # Show this screen.
    --version           # Show version.

Description:
    Allows the user to load the various OWT wafer map files and displayes
    them.
"""

# ---------------------------------------------------------------------------
### Imports
# ---------------------------------------------------------------------------
# Standard Library
import configparser
import itertools
import math
import os
import os.path as osp

# Third-Party
from docopt import docopt
import numpy as np
import wafer_map.wm_core as wm_core
import wafer_map.gen_fake_data as gen_fake_data
import wafer_map.wm_info as wm_info
import wx
import wx.lib.plot as wxplot

# Package / Application
try:
    # Imports used for unittests
    from . import mask_constants
    from . import (__project_name__,
                   __version__,
                   )
#    logging.debug("Imports for UnitTests")
except SystemError:
    try:
        # Imports used by Spyder
        import mask_constants
        from __init__ import (__project_name__,
                              __version__,
                              )
#        logging.debug("Imports for Spyder IDE")
    except ImportError:
         # Imports used by cx_freeze
        from owt_wm_view import mask_constants
        from owt_wm_view import (__project_name__,
                                 __version__,
                                 )
#        logging.debug("imports for Executable")


# ---------------------------------------------------------------------------
### Module Constants
# ---------------------------------------------------------------------------
MASK_PATH = "Z:\\Software\\LabView\\OWT\\masks"
__window_title__ = "{} v{}".format(__project_name__, __version__)

# ---------------------------------------------------------------------------
### Classes
# ---------------------------------------------------------------------------

class MainApp(object):
    """ Main Application """
    def __init__(self):
        self.app = wx.App()
        self.frame = MainUI()
        self.frame.Show()
        self.app.MainLoop()


class MainUI(wx.Frame):
    """ Main Window """
    def __init__(self):
        wx.Frame.__init__(self,
                          parent=None,
                          id=wx.ID_ANY,
                          title=__window_title__,
                          size=(1100, 600),
                          )
        self.init_ui()

    def init_ui(self):
        """ Init the UI Components """
        self.menu_bar = wx.MenuBar()
        self._create_menus()
        self._create_menu_items()
        self._add_menu_items()
        self._add_menus()
        self._bind_events()

        # Initialize default states
        self.mv_outline.Check()
        self.mv_crosshairs.Check()
        self.mv_legend.Check()

        self.panel = MainPanel(self)

        # Set the MenuBar and create a status bar (easy thanks to wx.Frame)
        self.SetMenuBar(self.menu_bar)
        self.CreateStatusBar()

    def _create_menus(self):
        """ Create each menu for the menu bar """
        self.mfile = wx.Menu()
        self.medit = wx.Menu()
        self.mview = wx.Menu()
        self.mopts = wx.Menu()

    def _create_menu_items(self):
        """ Create each item for each menu """
        ### Menu: File (mf_) ###
        self.mf_close = wx.MenuItem(self.mfile,
                                    wx.ID_ANY,
                                    "&Close\tCtrl+Q",
                                    "TestItem",
                                    )

        ### Menu: Edit (me_) ###
        self.me_redraw = wx.MenuItem(self.medit,
                                     wx.ID_ANY,
                                     "&Redraw",
                                     "Force Redraw",
                                     )

        ### Menu: View (mv_) ###
        self.mv_zoomfit = wx.MenuItem(self.mview,
                                      wx.ID_ANY,
                                      "Zoom &Fit\tHome",
                                      "Zoom to fit",
                                      )
        self.mv_crosshairs = wx.MenuItem(self.mview,
                                         wx.ID_ANY,
                                         "Crosshairs\tC",
                                         "Show or hide the crosshairs",
                                         wx.ITEM_CHECK,
                                         )
        self.mv_outline = wx.MenuItem(self.mview,
                                      wx.ID_ANY,
                                      "Wafer Outline\tO",
                                      "Show or hide the wafer outline",
                                      wx.ITEM_CHECK,
                                      )
        self.mv_legend = wx.MenuItem(self.mview,
                                     wx.ID_ANY,
                                     "Legend\tL",
                                     "Show or hide the legend",
                                     wx.ITEM_CHECK,
                                     )

        # Menu: Options (mo_) ###
        self.mo_test = wx.MenuItem(self.mopts,
                                   wx.ID_ANY,
                                   "&Test",
                                   "Nothing",
                                   )
        self.mo_high_color = wx.MenuItem(self.mopts,
                                         wx.ID_ANY,
                                         "Set &High Color",
                                         "Choose the color for high values",
                                         )
        self.mo_low_color = wx.MenuItem(self.mopts,
                                        wx.ID_ANY,
                                        "Set &Low Color",
                                        "Choose the color for low values",
                                        )

    def _add_menu_items(self):
        """ Appends MenuItems to each menu """
        self.mfile.Append(self.mf_close)

        self.medit.Append(self.me_redraw)

        self.mview.Append(self.mv_zoomfit)
        self.mview.AppendSeparator()
        self.mview.Append(self.mv_crosshairs)
        self.mview.Append(self.mv_outline)
        self.mview.Append(self.mv_legend)

        self.mopts.Append(self.mo_test)
        self.mopts.Append(self.mo_high_color)
        self.mopts.Append(self.mo_low_color)

    def _add_menus(self):
        """ Appends each menu to the menu bar """
        self.menu_bar.Append(self.mfile, "&File")
        self.menu_bar.Append(self.medit, "&Edit")
        self.menu_bar.Append(self.mview, "&View")
        self.menu_bar.Append(self.mopts, "&Options")

    def _bind_events(self):
        """ Binds events to varoius MenuItems """
        self.Bind(wx.EVT_MENU, self.on_quit, self.mf_close)
        self.Bind(wx.EVT_MENU, self.zoom_fit, self.mv_zoomfit)
        self.Bind(wx.EVT_MENU, self.toggle_crosshairs, self.mv_crosshairs)
        self.Bind(wx.EVT_MENU, self.toggle_outline, self.mv_outline)
        self.Bind(wx.EVT_MENU, self.toggle_legend, self.mv_legend)
        self.Bind(wx.EVT_MENU, self.change_high_color, self.mo_high_color)
        self.Bind(wx.EVT_MENU, self.change_low_color, self.mo_low_color)

    def on_quit(self, event):
        """ Actions for the quit event """
        self.Close(True)

    def zoom_fit(self, event):
        """ Call the WaferMapPanel.zoom_fill() method """
        print("Frame Event!")
        self.panel.wm_panel.zoom_fill()

    def toggle_crosshairs(self, event):
        """ Call the WaferMapPanel toggle_crosshairs() method """
        self.panel.wm_panel.toggle_crosshairs()

    def toggle_outline(self, event):
        """ Call the WaferMapPanel.toggle_outline() method """
        self.panel.wm_panel.toggle_outline()

    def toggle_legend(self, event):
        """ Call the WaferMapPanel.toggle_legend() method """
        self.panel.wm_panel.toggle_legend()

    def change_high_color(self, event):
        print("High color menu item clicked!")
        cd = wx.ColourDialog(self)
        cd.GetColourData().SetChooseFull(True)

        if cd.ShowModal() == wx.ID_OK:
            new_color = cd.GetColourData().Colour
            print("The color {} was chosen!".format(new_color))
            self.panel.wm_panel.on_color_change({'high': new_color,
                                                 'low': None})
            self.panel.wm_panel.Refresh()
        else:
            print("no color chosen :-(")
        cd.Destroy()

    def change_low_color(self, event):
        print("Low Color menu item clicked!")
        cd = wx.ColourDialog(self)
        cd.GetColourData().SetChooseFull(True)

        if cd.ShowModal() == wx.ID_OK:
            new_color = cd.GetColourData().Colour
            print("The color {} was chosen!".format(new_color))
            self.panel.wm_panel.on_color_change({'high': None,
                                                 'low': new_color})
            self.panel.wm_panel.Refresh()
        else:
            print("no color chosen :-(")
        cd.Destroy()


class MainPanel(wx.Panel):
    """ Main Panel within Main Window """
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.parent = parent
        self.mask_names = []
        self.wafer_maps = []
        self.mask_data = None

        self.init_data()
        self.init_ui()

    def init_data(self):
        """ Gets a list of all the masks available """
        self.mask_names = sorted([osp.splitext(_m)[0]
                                  for _m
                                  in os.listdir(MASK_PATH)
                                  if _m.endswith(".ini")])

    def init_ui(self):
        """ Init the UI Components """
        # Create our list boxes
        self.mask_lbl = wx.StaticText(self, wx.ID_ANY, label="Mask")
        self.mask_lb = wx.ListBox(parent=self,
                                  id=wx.ID_ANY,
                                  size=(150, 200),
                                  choices=self.mask_names,
                                  style=wx.LB_SINGLE,
                                  )

        self.map_lbl = wx.StaticText(self, wx.ID_ANY, label="Map")
        self.map_lb = wx.ListBox(parent=self,
                                 id=wx.ID_ANY,
                                 size=(150, 150),
                                 choices=self.wafer_maps,
                                 style=wx.LB_SINGLE,
                                 )

        # For now, generate some fake data and plot it.
        wafer_info, xyd = gen_fake_data.generate_fake_data(dtype='discrete')
        self.wm_panel = wm_core.WaferMapPanel(self,
                                              xyd,
                                              wafer_info,
                                              data_type='discrete',
                                              )

        self.stats_block= StatsBlock(self)

        # Create the radius plots
        radius_sqrd_data = list(
           (wafer_info.die_size[0] * (wafer_info.center_xy[0] - die[0]))**2
           + (wafer_info.die_size[1] * (wafer_info.center_xy[1] - die[1]))**2
           for die in xyd)
        radius_data = list(math.sqrt(item) for item in radius_sqrd_data)
        self.radius_plots = RadiusPlots(self, radius_data)

        # Create our layout manager
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox_plots = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.mask_lbl, 0, wx.LEFT, 5)
        self.vbox.Add(self.mask_lb, 0, wx.LEFT, 5)
        self.vbox.Add((-1, 10))
        self.vbox.Add(self.map_lbl, 0, wx.LEFT, 5)
        self.vbox.Add(self.map_lb, 0, wx.LEFT, 5)
        self.vbox.Add((-1, 10))
        self.vbox.Add(self.stats_block, 1,
                      wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, 5)
        self.hbox.Add(self.vbox, 0, wx.EXPAND)
        self.hbox.Add(self.wm_panel, 2, wx.EXPAND)
        self.vbox_plots.Add(self.radius_plots, 1, wx.EXPAND)
        self.hbox.Add(self.vbox_plots, 1, wx.EXPAND)

        self.SetSizer(self.hbox)

        # Bind events
        self._bind_events()

    def _bind_events(self):
        """ Binds events to various controls """
        self.mask_lb.Bind(wx.EVT_LISTBOX, self._on_mask_change)
        self.map_lb.Bind(wx.EVT_LISTBOX, self._on_map_change)

    def _on_mask_change(self, event):
        """ Fires when user selects a different item in the Mask ListBox """
        mask = self.mask_lb.GetStringSelection()
        print("Mask Changed to: {}".format(mask))
        self._update_maps(mask)

    def _update_maps(self, mask):
        """
        Reads the mask file for the selected mask and updates the Map
        ListBox with all of the wafer maps. Assumes 150mm wafer.
        """
        # Create an instance of the Mask class
        self.mask_data = Mask(mask)

        # Edit the Map ListBox: First Clear it, then insert new items
        self.map_lb.Clear()
        self.map_lb.AppendItems(self.mask_data.map_names)

    def _on_map_change(self, event):
        """
        Updates the wafer map display with the selected map.

        I'm thinking... Perhaps I have the "Every" map displayed as white
        boxes and then have the selected map highlighted as some color.
        """
        # First, get the Every map and update the wafer map with it.
        map_name = self.map_lb.GetStringSelection()
        wfrmap = self.mask_data.maps[map_name]
        print("Map Changed to: {}".format(map_name))
#        wfrmap = self.mask_data.maps['Every']

        # Create a new xyd list based on the mask
        self.xyd = [(_c, _r, "Every") for _r, _c in wfrmap]
#        self.center_xy = (10, 10)
        self.wafer_info = wm_info.WaferInfo(self.mask_data.die_xy,
                                            self.mask_data.center_xy,
                                            self.mask_data.dia,
                                            4.5,
                                            4.5)

        # All these things just so that I can update the map...
        self.wm_panel.canvas.InitAll()
        self.wm_panel._clear_canvas()
        self.wm_panel.die_size = self.mask_data.die_xy
        self.wm_panel.xyd = self.xyd
        self.wm_panel.wafer_info = self.wafer_info
        self.wm_panel.grid_center = self.mask_data.center_xy
        self.wm_panel.xyd_dict = wm_core.xyd_to_dict(self.xyd)
        self.wm_panel._create_legend()
        self.wm_panel.draw_die()
        self.wm_panel.draw_die_center()
        self.wm_panel.draw_wafer_objects()
        self.wm_panel.zoom_fill()

        self.stats_block.update_stats(self.xyd)

        radius_sqrd_data = list(
           (self.wafer_info.die_size[0] * (self.wafer_info.center_xy[0] - die[0]))**2
           + (self.wafer_info.die_size[1] * (self.wafer_info.center_xy[1] - die[1]))**2
           for die in self.xyd)
        new_radius_data = list(math.sqrt(item) for item in radius_sqrd_data)
        self.radius_plots.update(new_radius_data)

        self.Refresh()
        self.Update()


class RadiusPlots(wx.Panel):
    """ A container for the two radius histograms """
    def __init__(self, parent, radius_data):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.radius_data = radius_data
        self._init_ui()

        self._bind_events()

    def _init_ui(self):
        """ """
        # create the items
        self.lin_binspec = range(0, 81, 5)

        # bins of equal area, area = 2000 mm^2
        self.eq_area_binspec = [0, 25.2313, 35.6825, 43.7019,
                                50.4627, 56.419, 61.8039,
                                66.7558, 71.365, 75.694]

        self.radius_plot = Histogram(self,
                                     self.radius_data,
                                     self.lin_binspec,
                                     "Bin Size = 5mm",
                                     "Radius (mm)",
                                     )
        self.eq_area_plot = Histogram(self,
                                      self.radius_data,
                                      self.eq_area_binspec,
                                      "BinSize = 2000 mm^2",
                                      "Radius (mm)",
                                      )

        # Create the layout manager
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.radius_plot, 1, wx.EXPAND)
        self.vbox.Add(self.eq_area_plot, 1, wx.EXPAND)
        self.SetSizer(self.vbox)

    def _bind_events(self):
        """ """
        pass

    def update(self, data):
        """ Updates the two radius plots """
        self.radius_plot.update(data, self.lin_binspec)
        self.eq_area_plot.update(data, self.eq_area_binspec)


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


class Histogram(wxplot.PlotCanvas):
    """
    A homebrewed histogram plot

    data must be a 1d list or tuple of floats or integers.

    binspec must be a 1d list or tuple of floats or integers.

    binspec defines the bin cutoff points
    For example, binspec = [0, 1, 2, 3, 4] would result in 6 bins:
        x < 0
        0 <= x < 1
        1 <= x < 2
        3 <= x < 3
        3 <= x < 4
        x >= 4

    """
    def __init__(self, parent, data, binspec,
                 title="Histogram", x_label="Bin", y_label="Count"):
        wxplot.PlotCanvas.__init__(self, parent)
        self.parent = parent
        self.data = data
        self.binspec = binspec
        self.hist_data = None
        self.title = title
        self.x_label = x_label
        self.y_label = y_label

#        self._init_data()

#        self._init_ui()
        self.update(self.data, self.binspec)

    def _init_ui(self):
        pass

    def _init_data(self):
        pass

    def update(self, data, binspec):
        self.Clear()

        # other stuff uses numpy so I can too.
        hist, edges = np.histogram(data, binspec)

        bars = []
        for n, (count, (low, high)) in enumerate(zip(hist, pairwise(edges))):

            pts = [(low, 0), (low, count)]
            ln = wxplot.PolyLine(pts,
                                 colour='blue',
                                 width=3,
                                 )
            bars.append(ln)

            # hack to get things to look like a "bar"...
            pts2 = [(high, 0), (high, count)]
            ln2 = wxplot.PolyLine(pts2,
                                  colour='blue',
                                  width=3,
                                  )
            bars.append(ln2)
            pts3 = [(low, count), (high, count)]
            ln3 = wxplot.PolyLine(pts3,
                                  colour='blue',
                                  width=3,
                                  )
            bars.append(ln3)

        bars = [wxplot.PolyHistogram(hist, edges)]

        plot = wxplot.PlotGraphics(bars,
                                   title=self.title,
                                   xLabel=self.x_label,
                                   yLabel=self.y_label,
                                   )

        self.XSpec = (0, 75)

        self.EnableGrid = True
        self.Draw(plot)


class LabeledListBox(wx.Panel):
    """ A simple Labeled List Box """
    def __init__(self, parent, label_text, *args, **kwargs):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.label_text = label_text
        self.args = args
        self.kwargs = kwargs
        self.init_ui()

    def init_ui(self):
        """ Init UI components """
        self.lbl = wx.StaticText(self, wx.ID_ANY, label=self.label_text)
        self.lb = wx.ListBox(self, *self.args, **self.kwargs)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.lbl)
        self.vbox.Add(self.lb)

        self.SetSizer(self.vbox)


class StatsBlock(wx.Panel):
    """
    A Stats block
    """
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.data = None

        self.fmt_str = "{lbl}: {val: >20.6e}"
        self.percentiles = [0.05, 0.25, 0.5, 0.75, 0.95]
        self.stat_str = ""

        self.init_ui()

    def init_ui(self):
        """ Init the UI components """
        # Create our items. I will updated the static texts with the values,
        # so I don't need other widgets.
        self.stat_str_ui = wx.StaticText(self, wx.ID_ANY,
                                         label="No file loaded",
                                         size=(150, 80),
                                         )

        font = wx.Font(10,
                       wx.FONTFAMILY_TELETYPE,
                       wx.FONTSTYLE_NORMAL,
                       wx.FONTWEIGHT_NORMAL,
                       )
        self.stat_str_ui.SetFont(font)

        self.sbox = wx.StaticBox(self, wx.ID_ANY, "Statistics")
        self.svbox = wx.StaticBoxSizer(self.sbox, wx.VERTICAL)

        self.svbox.Add(self.stat_str_ui, 1, wx.EXPAND)

        self.SetSizer(self.svbox)

    def update_stats(self, data):
        """
        Updates the data statistics.

        Parameters:
        -----------
        xyd : list of tuples
            The grid (X, Y, Data) list

        Returns:
        --------
        None

        """
        die_count = len(data)
        self.stat_str_ui.SetLabel("Die Count: {}".format(die_count))


# TODO: too many attributes
class Mask(object):
    """
    Upon init, reads an OWT mask file and stores things to memory.
    """
    def __init__(self, mask):
        self.mask = mask
        self.mask_path = MASK_PATH
        self.mask_filename = self.mask + ".ini"
        self.mask_file = osp.join(self.mask_path, self.mask_filename)
        self.mask_info = None
        self.mask_info_names = None
        self.maps = None
        self.map_names = None
        self.devices = None
        self.device_names = None

        self.read_mask_file()

    def read_mask_file(self):
        """ Reads the wafer maps from the 150mm section """
        parser = configparser.RawConfigParser()
        parser.optionxform = str        # Make keys Case-sensitive
        parser.read(self.mask_file)

        self._extract_mask_info(parser.items("Mask"))

        # Try all of the wafer diameters. I only want the biggest wafer size.
        # TODO: replace with douglib.utils.try_again
        args = ["150mm", "100mm", "50mm"]
        for arg in args:
            try:
                self._extract_maps(parser.items(arg))
                self.dia = int(arg[:-2])
                break
            except configparser.NoSectionError:
                continue
        else:
            # for loop never 'break', so there was always an error. Raise it.
            error_txt = "Why are there no sections?"
            raise configparser.NoSectionError(error_txt)

        self.devices = dict(parser.items("Devices"))
        self.device_names = sorted(self.devices.keys())

    def _extract_mask_info(self, mask_info):
        """ Extracts mask_info items from the list return by parser """
        self.mask_info = dict(mask_info)
        self.mask_info_names = sorted(self.mask_info.keys())
        self.die_x = float(self.mask_info["Die X"])
        self.die_y = float(self.mask_info["Die Y"])
        self.die_xy = (self.die_x, self.die_y)
        self.flat_loc = int(self.mask_info["Flat"])
        mask_enum = mask_constants.lookup(self.mask_info['Mask'][1:-1])
        self.center_xy = mask_enum.center_xy
        print("Center XY: {}".format(self.center_xy))

    def _extract_maps(self, maps):
        """
        Removes the unnecessary map info from the "150mm" section. This info
        is the Rows, Cols, Home Row, Home Col, Start Row, Start Col. These
        items are saved for posterity, but I don't think they're needed.
        """
        self.maps = dict(maps)
        self.row_count = dictpop(self.maps, "Rows")
        self.col_count = dictpop(self.maps, "Cols")
        self.home_row = dictpop(self.maps, "Home Row")
        self.home_col = dictpop(self.maps, "Home Col")
        self.start_row = dictpop(self.maps, "Start Row")
        self.start_col = dictpop(self.maps, "Start Col")
        self.map_names = sorted(self.maps.keys())

        for key in self.map_names:
            self.maps[key] = convert_map_list(self.maps[key])


def invert_wafer_map(xy_list):
    """
    Inverts a wafer map (list of (x, y) coordinate pairs).

    Needed because the OWT files use an exclusion list while everything else
    uses an *inclusion* list.
    """
    # First, find the min and max X and Y coordinates
    min_x = min([_x for _x, _y in xy_list])         # won't it always be 1?
    max_x = max([_x for _x, _y in xy_list])
    min_y = min([_y for _x, _y in xy_list])         # won't it always be 1?
    max_y = max([_y for _x, _y in xy_list])

    # Then create two lists for all possible points
    all_x = range(1, max_x + 1)
    all_y = range(1, max_y + 1)
    all_xy = {(_x, _y) for _y in all_y for _x in all_x}     # Note it's a set

    # now make our original xy_list into a set and subtract it from all_xy
    inverted = list(all_xy - set(xy_list))
    return inverted


def convert_map_list(string):
    """
    Converts a map string to a list of (X, Y) coord pairs.

    The string looks like
    "1,1; 1,2; 1,3; 1,4; 1,5; 1,6; 1,7; 1,8; 1,9; 1,10"
    """
    xy_list = []
    for pair in string[1:-1].split("; "):
        try:
            xy_list.append(tuple(map(int, pair.split(","))))
        except ValueError:
            print("Can't convert '{}'".format(pair))
            raise

    return invert_wafer_map(xy_list)


def dictpop(dictionary, item):
    """ Deletes an item from a dictionary and returns it. """
    retval = dictionary[item]
    del dictionary[item]
    return retval


def main():
    """ Main Code """
    docopt(__doc__, version=__version__)
    MainApp()


if __name__ == "__main__":
    main()
