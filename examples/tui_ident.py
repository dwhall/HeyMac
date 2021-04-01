#!/usr/bin/env python3

"""
Copyright 2021 Dean Hall.  See LICENSE for details.

The Text User Interface Identity model and view
"""

from asciimatics.widgets import Button, CheckBox, Divider, Frame, Label, \
        Layout, Text, TextBox, Widget
from asciimatics.exceptions import NextScene

from heymac.utl.ham_ident import HamIdent


class IdentModel(object):

    def device_cred_exists(self):
        try:
            info = HamIdent.get_info_from_json_cred("HeyMac")
        except:
            return False
        return bool(info)


    def personal_cert_exists(self):
        return HamIdent.cert_file_exists()


    def get_ident(self):
        try:
            ident = HamIdent.get_info_from_cert()
        except:
            ident = {}
        try:
            cred = HamIdent.get_info_from_json_cred("HeyMac")
        except:
            cred = {}
        if '-' in cred.get("callsign", ""):
            cred["ssid"] = cred["callsign"].split("-")[1]
            del cred["callsign"]
        ident.update(cred)
        return ident


    def get_summary(self):
        ident = self.get_ident()
        return ident.get("callsign", "No Ident")


    def apply(self, info):
        if self.personal_cert_exists():
            ident = HamIdent("HeyMac")
            ssid = info["ssid"]
            passphrase = info["dev_pass"].encode()
            ident.gen_device_credentials(ssid, passphrase)
        else:
            ident = HamIdent()
            passphrase = info["person_pass"].encode()
            ident.gen_personal_credentials(info, passphrase)


    def fields_are_equal_to(self, d):
        ident_fields = (
                "cmn_name", "callsign", "email", "country", "province",
                "postalcode", "ssid")
        ident = self.get_ident()
        for fld in ident_fields:
            if ident.get(fld) != d.get(fld):
                return False
        return True


class IdentView(Frame):
    def __init__(self, screen, ident_model):
        super().__init__(screen,
                         screen.height,
                         screen.width,
                         title="Identity",)
        self._ident_model = ident_model

        MAX_LEN_CALLSIGN = 12
        MAX_LEN_DEV_ID = 4
        MAX_LEN_COUNTRY = 3

        # Personal input fields
        # Col 0
        layout1 = Layout([1,4,4], fill_frame=True)
        self.add_layout(layout1)
        layout1.add_widget(Label("Personal:"), 0)
        layout1.add_widget(Divider(draw_line=False, height=7), 0)
        layout1.add_widget(Divider(draw_line=True, height=1), 0)

        # Col 1
        layout1.add_widget(Text(label="Common name:",
                                on_change=self._on_change,
                                name="cmn_name"), 1)
        layout1.add_widget(Text(label="Callsign:",
                                on_change=self._on_change,
                                name="callsign",
                                max_length=MAX_LEN_CALLSIGN), 1)
        layout1.add_widget(Text(label="Email:",
                                on_change=self._on_change,
                                name="email"), 1)
        layout1.add_widget(Text(label="Country:",
                                on_change=self._on_change,
                                name="country",
                                max_length=MAX_LEN_COUNTRY), 1)
        layout1.add_widget(Text(label="State/province:",
                                on_change=self._on_change,
                                name="province"), 1)
        layout1.add_widget(Text(label="Postal/zip code:",
                                on_change=self._on_change,
                                name="postalcode"), 1)
        layout1.add_widget(Divider(draw_line=False, height=1), 1)
        layout1.add_widget(Text(label="Passphrase:",
                                on_change=self._on_change,
                                name="person_pass",
                                validator=self._validate_pwd,
                                hide_char='*'), 1)
        layout1.add_widget(Divider(draw_line=True, height=1), 1)

        # Col 2
        txt = TextBox(8, line_wrap=True, readonly=True)
        txt.disabled = True
        txt.value = ["Info to create a personal X.509 crypto certficate.  "
                    "You must input your callsign and should input "
                    "correct data in the other fields to increase trust."]
        layout1.add_widget(txt, 2)
        layout1.add_widget(Divider(draw_line=True, height=1), 2)

        # Device input fields
        # Col 0
        layout1.add_widget(Label("Device:", name="dev_lbl"), 0)
        layout1.add_widget(Divider(draw_line=False, height=2), 0)
        layout1.add_widget(Divider(draw_line=True, height=1), 0)

        # Col 1
        layout1.add_widget(Text(label="SSID:",
                                on_change=self._on_change,
                                name="ssid",
                                max_length=MAX_LEN_DEV_ID), 1)
        layout1.add_widget(Divider(draw_line=False, height=1), 1)
        layout1.add_widget(Text(label="Passphrase:",
                                on_change=self._on_change,
                                name="dev_pass",
                                validator=self._validate_pwd,
                                hide_char='*'), 1)
        layout1.add_widget(Divider(draw_line=True, height=1), 1)

        # Col 2
        txt = TextBox(3, line_wrap=True, readonly=True)
        txt.disabled = True
        txt.value = ["This information is used to create device credentials. "
                    "Each device should have its own three-digit SSID."]
        layout1.add_widget(txt, 2)
        layout1.add_widget(Divider(draw_line=True, height=1), 2)


        # Output fields
        layout1.add_widget(Label("Output:"), 0)
        layout1.add_widget(CheckBox("Personal cert exists",
                                    name="cert_exists",
                                    disabled=True), 1)
        layout1.add_widget(CheckBox("Device cred exists",
                                    name="cred_exists",
                                    disabled=True), 1)
        layout1.add_widget(Divider(draw_line=False,
                                   height=Widget.FILL_FRAME), 1)

        # Buttons
        layout2 = Layout([1, 1, 1, 1], fill_frame=False)
        self.add_layout(layout2)
        layout2.add_widget(Button("Apply",
                                  on_click=self._on_click_apply,
                                  name="btn_apply",
                                  disabled=True), 1)
        layout2.add_widget(Button("Cancel",
                                  on_click=self._on_click_cancel), 2)
        self.fix()


    def reset(self):
        super().reset()
        self.data = self._ident_model.get_ident()


    def _on_change(self):
        self.save()
        self._update_disabled()

    def _update_disabled(self):
        # Disable device fields until personal cert exists
        dev_disabled = not self._ident_model.personal_cert_exists()
        self.find_widget("dev_lbl").disabled = dev_disabled
        self.find_widget("ssid").disabled = dev_disabled
        self.find_widget("dev_pass").disabled = dev_disabled

        # Apply button is disabled when cert exists and
        # input fields match existing cert/cred info
        self.find_widget("btn_apply").disabled = self._ident_model.personal_cert_exists() \
                and self._ident_model.fields_are_equal_to(self.data)

        self.find_widget("cert_exists").value = self._ident_model.personal_cert_exists()
        self.find_widget("cred_exists").value = self._ident_model.device_cred_exists()


    def _build_info_from_view(self):
        return {}


    def _on_click_cancel(self):
        raise NextScene("Messages")


    def _on_click_apply(self):
        self.save()
        self._ident_model.apply(self.data)
        self._update_disabled()


    def _validate_pwd(self, s):
        return len(s) > 0
