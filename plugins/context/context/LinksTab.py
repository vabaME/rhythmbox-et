# -*- Mode: python; coding: utf-8; tab-width: 8; indent-tabs-mode: t; -*-
#
# Copyright (C) 2010 Kenny Meyer <knny.myer@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# The Rhythmbox authors hereby grant permission for non-GPL compatible
# GStreamer plugins to be used and distributed together with GStreamer
# and Rhythmbox. This permission is above and beyond the permissions granted
# by the GPL license by which Rhythmbox is covered. If you modify this code
# you may extend this exception to your version of the code, but you are not
# obligated to do so. If you do not wish to do so, delete this exception
# statement from your version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

import rhythmdb
import gtk, gobject
import os
import cgi
import urllib

from gettext import gettext as _

import webkit
from mako.template import Template


class LinksTab (gobject.GObject):

    __gsignals__ = {
        'switch-tab' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                                (gobject.TYPE_STRING,))
    }

    def __init__ (self, shell, buttons, ds, view):
        gobject.GObject.__init__ (self)
        self.shell      = shell
        self.sp         = shell.get_player ()
        self.db         = shell.get_property ('db')
        self.buttons    = buttons

        self.button     = gtk.ToggleButton (_("Links"))
        self.datasource = ds
        self.view       = view
        self.artist     = None
        self.album      = None

        self.button.show()
        self.button.set_relief( gtk.RELIEF_NONE )
        self.button.set_focus_on_click(False)
        self.button.connect ('clicked',
            lambda button : self.emit('switch-tab', 'links'))
        buttons.pack_start (self.button, True, True)

    def activate (self):
        print "activating Links Tab"
        self.button.set_active(True)
        self.reload ()

    def deactivate (self):
        print "deactivating Links Tab"
        self.button.set_active(False)

    def reload (self):
        entry = self.sp.get_playing_entry ()
        if entry is None:
            return None

        artist = self.db.entry_get (entry, rhythmdb.PROP_ARTIST)
        album = self.db.entry_get (entry, rhythmdb.PROP_ALBUM)
        self.artist = artist
        self.album = album

        self.datasource.set_artist (artist)
        self.datasource.set_album (album)

        self.view.load_links (self.datasource)


class LinksView (gobject.GObject):

    def __init__ (self, shell, plugin, webview):
        gobject.GObject.__init__ (self)
        self.shell    = shell
        self.plugin   = plugin
        self.webview  = webview
        self.file     = ""
        plugindir = os.path.split(plugin.find_file ('context.rb-plugin'))[0]
        self.basepath = "file://" + urllib.pathname2url (plugindir)

    def load_links (self, ds):
        print "Loading links into webview"
        self.path = self.plugin.find_file('tmpl/links-tmpl.html')
        self.images = self.basepath + '/img/links/'
        self.styles = self.basepath + '/tmpl/main.css'
        self.template = Template (filename = self.path, 
                                  module_directory = '/tmp/context/')

        self.file = self.template.render (error      = ds.get_error (),
                                          artist     = ds.get_artist(),
                                          album      = ds.get_album (),
                                          art_links  = ds.get_artist_links (),
                                          alb_links  = ds.get_album_links (),
                                          images     = self.images,
                                          stylesheet = self.styles )

        self.webview.load_string (self.file, 'text/html', 'utf-8', self.basepath)


class LinksDataSource (gobject.GObject):

    def __init__ (self, db):
        gobject.GObject.__init__ (self)

        self.db = db
        self.entry = None
        self.error = None

        self.artist = None
        self.album = None

    def set_artist (self, artist):
        self.artist = artist

    def get_artist (self):
        return self.artist

    def set_album (self, album):
        self.album = album

    def get_album (self):
        return self.album

    def get_artist_links (self):
        """
        Return a dictionary with artist URLs to popular music databases and
        encyclopedias.
        """
        artist = self.get_artist()
        if artist is not "" and artist is not None:
            wpartist = artist.replace(" ", "_")
            artist = urllib.quote_plus (artist)
            artist_links = {
                "Wikipedia" : "http://www.wikipedia.org/wiki/%s" % wpartist,
                "Discogs"  : "http://www.discogs.com/artist/%s" % artist,
                "Allmusic" : "http://www.allmusic.com/search/artist/%s" % artist
            }
            return artist_links
        return None

    def get_album_links (self):
        """
        Return a dictionary with album URLs to popular music databases and
        encyclopedias.
        """
        album = self.get_album()
        if album is not "" and album is not None:
            wpalbum = album.replace(" ", "_")
            album = urllib.quote_plus (album)
            album_links = {
                "Wikipedia" : "http://www.wikipedia.org/wiki/%s" % wpalbum,
                "Discogs" : "http://www.discogs.com/search?type=album&q=%s&f=html" % album,
                "Allmusic" : "http://allmusic.com/search/album/%s" % album
            }
            return album_links
        return None

    def get_error (self):
        if self.get_artist() is "":
            return _("No artist specified.")