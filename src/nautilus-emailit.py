#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This file is part of nautilus-emailit
#
# Copyright (C) 2016-2017 Lorenzo Carbonell
# lorenzo.carbonell.cerezo@gmail.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
#
import gi
try:
    gi.require_version('Gtk', '3.0')
    gi.require_version('Nautilus', '3.0')
except Exception as e:
    print(e)
    exit(-1)
import os
from urllib import unquote_plus
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import Nautilus as FileManager
import getpass
import socket
import shlex
import subprocess

APPNAME = 'nautilus-emailit'
ICON = 'nautilus-emailit'
VERSION = '$VERSION$'

_ = str


class EmailItDialog(Gtk.Dialog):

    def __init__(self, window, email_from=None, email_to=None, subject=None,
                 message=None):
        Gtk.Dialog.__init__(self, 'EmailIt', window, Gtk.DialogFlags.MODAL |
                            Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                             Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_size_request(200, 300)
        frame = Gtk.Frame()
        frame.set_border_width(5)
        grid = Gtk.Grid()
        grid.set_border_width(5)
        grid.set_column_spacing(5)
        grid.set_row_spacing(5)
        frame.add(grid)
        self.get_content_area().add(frame)
        label = Gtk.Label(_('From')+' :')
        label.set_xalign(0)
        grid.attach(label, 0, 0, 1, 1)
        self.email_from = Gtk.Entry()
        grid.attach(self.email_from, 1, 0, 1, 1)
        self.show_all()
        label = Gtk.Label(_('To')+' :')
        label.set_xalign(0)
        grid.attach(label, 0, 1, 1, 1)
        self.email_to = Gtk.Entry()
        self.email_to.set_width_chars(50)
        grid.attach(self.email_to, 1, 1, 1, 1)
        label = Gtk.Label(_('Subject')+' :')
        label.set_xalign(0)
        grid.attach(label, 0, 2, 1, 1)
        self.email_subject = Gtk.Entry()
        grid.attach(self.email_subject, 1, 2, 1, 1)
        label = Gtk.Label(_('Message')+' :')
        label.set_xalign(0)
        grid.attach(label, 0, 3, 1, 1)
        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        scrolledwindow.set_hexpand(True)
        scrolledwindow.set_vexpand(True)
        grid.attach(scrolledwindow, 0, 4, 2, 2)
        self.email_message = Gtk.TextView()
        scrolledwindow.add(self.email_message)
        if email_from is None:
            email_from = '%s@%s.com' % (getpass.getuser(),
                                        socket.gethostname())
        if subject is None:
            subject = _('Email it with nautilus-emailit')
        if message is None:
            message = _('This email was send with nautilus-emailit')
        self.email_from.set_text(email_from)
        self.email_subject.set_text(subject)
        textbuffer = self.email_message.get_buffer()
        textbuffer.set_text(message)

        self.email_to.grab_focus()
        self.email_to.connect('key-press-event', self.on_key_press_in_email_to)
        self.show_all()

    def on_key_press_in_email_to(self, widget, anevent):
        print(widget, anevent.keyval)
        if anevent.keyval == 65421 or anevent.keyval == 65293:
            self.response(Gtk.ResponseType.ACCEPT)

    def get_from(self):
        return self.email_from.get_text()

    def get_to(self):
        return self.email_to.get_text()

    def get_subject(self):
        return self.email_subject.get_text()

    def get_message(self):
        textbuffer = self.email_message.get_buffer()
        return textbuffer.get_text(textbuffer.get_start_iter(),
                                   textbuffer.get_end_iter(),
                                   True)


def get_files(files_in):
    files = []
    for file_in in files_in:
        print(file_in)
        file_in = unquote_plus(file_in.get_uri()[7:])
        if os.path.isfile(file_in):
            files.append(file_in)
    return files


def send_mail(email_to, email_from=None, subject=None, message=None, files=[]):
    if email_from is None:
        email_from = '%s@%s.com' % (getpass.getuser(), socket.gethostname())
    if subject is None:
        subject = _('Email it with nautilus-emailit')
    if message is None:
        message = _('This email was send with nautilus-emailit')
    if len(files) > 0:
        list_of_files = ''
        for afile in files:
            list_of_files += '"%s" ' % (afile)
        runtime = 'sendemail -f %s -t %s -u "%s" -m "%s" -a %s' % (
            email_from,
            email_to,
            subject,
            message,
            list_of_files)
    else:
        runtime = 'sendemail -f %s -t %s -u "%s" -m "%s"' % (
            email_from,
            email_to,
            subject,
            message)
    print(runtime)
    args = shlex.split(runtime)
    process = subprocess.Popen(args, stdout=subprocess.PIPE)
    out, err = process.communicate()
    print(out, err)
    print('---------------')
    if out.find('successfully') > -1:
        return True
    return False


class EmailItMenuProvider(GObject.GObject, FileManager.MenuProvider):
    """
    Implements the 'Replace in Filenames' extension to the File Manager\
    right-click menu
    """

    def __init__(self):
        """
        File Manager crashes if a plugin doesn't implement the __init__\
        method
        """
        pass

    def all_are_files(self, items):
        for item in items:
            file_in = unquote_plus(item.get_uri()[7:])
            if not os.path.isfile(file_in):
                return False
        return True

    def emailit(self, menu, selected, window):
        files = get_files(selected)
        if len(files) > 0:
            eid = EmailItDialog(window)
            if eid.run() == Gtk.ResponseType.ACCEPT:
                email_to = eid.get_to()
                email_from = eid.get_from()
                subject = eid.get_subject()
                message = eid.get_message()
                eid.destroy()
                ans = send_mail(email_to=email_to,
                                email_from=email_from,
                                subject=subject,
                                message=message,
                                files=files)
                if ans is True:
                    dialog = Gtk.MessageDialog(
                        None,
                        0,
                        Gtk.MessageType.INFO,
                        Gtk.ButtonsType.OK,
                        _('Files were send'))
                    dialog.run()
                    dialog.destroy()
                else:
                    dialog = Gtk.MessageDialog(
                        None,
                        0,
                        Gtk.MessageType.ERROR,
                        Gtk.ButtonsType.OK,
                        _('Files were NOT send'))
                    dialog.run()
                    dialog.destroy()
                return
            eid.destroy()

    def get_file_items(self, window, sel_items):
        """
        Adds the 'Replace in Filenames' menu item to the File Manager\
        right-click menu, connects its 'activate' signal to the 'run'\
        method passing the selected Directory/File
        """
        if self.all_are_files(sel_items):
            if len(sel_items) > 1:
                label = _('Email them')
            else:
                label = _('Email it')

            top_menuitem = FileManager.MenuItem(
                name='EmailItMenuProvider::Gtk-emailit-top',
                label=label+'...',
                tip=_('Email files directly'))
            submenu = FileManager.Menu()
            top_menuitem.set_submenu(submenu)

            sub_menuitem_00 = FileManager.MenuItem(
                name='EmailItMenuProvider::Gtk-emailit-sub-01',
                label=label,
                tip=_('Email files directly'))
            sub_menuitem_00.connect('activate',
                                    self.emailit,
                                    sel_items,
                                    window)
            submenu.append_item(sub_menuitem_00)
            sub_menuitem_01 = FileManager.MenuItem(
                name='EmailItMenuProvider::Gtk-emailit-sub-02',
                label=_('About'),
                tip=_('About'))
            sub_menuitem_01.connect('activate', self.about, window)
            submenu.append_item(sub_menuitem_01)
            #
            return top_menuitem,
        return

    def about(self, widget, window):
        ad = Gtk.AboutDialog(parent=window)
        ad.set_name(APPNAME)
        ad.set_version(VERSION)
        ad.set_copyright('Copyrignt (c) 2016\nLorenzo Carbonell')
        ad.set_comments(APPNAME)
        ad.set_license('''
This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
''')
        ad.set_website('http://www.atareao.es')
        ad.set_website_label('http://www.atareao.es')
        ad.set_authors([
            'Lorenzo Carbonell <lorenzo.carbonell.cerezo@gmail.com>'])
        ad.set_documenters([
            'Lorenzo Carbonell <lorenzo.carbonell.cerezo@gmail.com>'])
        ad.set_icon_name(ICON)
        ad.set_logo_icon_name(APPNAME)
        ad.run()
        ad.destroy()

if __name__ == '__main__':
    eid = EmailItDialog()
    if eid.run() == Gtk.ResponseType.ACCEPT:
        print(eid.get_message())
