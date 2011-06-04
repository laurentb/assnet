# -*- coding: utf-8 -*-

# Copyright (C) 2011 Romain Bignon, Laurent Bachelier
#
# This file is part of ass2m.
#
# ass2m is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ass2m is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with ass2m. If not, see <http://www.gnu.org/licenses/>.

from email.mime.text import MIMEText
import smtplib
from email.Header import Header
from email.Utils import parseaddr, formataddr


class SMTP(smtplib.SMTP):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self.quit()
        except smtplib.SMTPServerDisconnected:
            pass


class Mail(object):
    def __init__(self, storage, template, sender, recipient, subject, smtp):
        from .template import build_lookup
        self.template = build_lookup(storage).get_template(template)
        self.sender = sender
        self.recipient = recipient
        self.subject = subject
        self.smtp = smtp
        self.vars = {}

    def send(self):
        body = self.template.render(**self.vars)

        header_charset = 'ISO-8859-1'

        # We must choose the body charset manually
        for body_charset in 'US-ASCII', 'ISO-8859-1', 'UTF-8':
            try:
                body.encode(body_charset)
            except UnicodeError:
                pass
            else:
                break
        sender_name, sender_addr = parseaddr(self.sender)
        recipient_name, recipient_addr = parseaddr(self.recipient)

        # We must always pass Unicode strings to Header, otherwise it will
        # use RFC 2047 encoding even on plain ASCII strings.
        sender_name = str(Header(unicode(sender_name), header_charset))
        recipient_name = str(Header(unicode(recipient_name), header_charset))

        # Make sure email addresses do not contain non-ASCII characters
        sender_addr = sender_addr.encode('ascii')
        recipient_addr = recipient_addr.encode('ascii')

        # Create the message ('plain' stands for Content-Type: text/plain)
        msg = MIMEText(body.encode(body_charset), 'plain', body_charset)
        msg['From'] = formataddr((sender_name, sender_addr))
        msg['To'] = formataddr((recipient_name, recipient_addr))
        msg['Subject'] = Header(unicode(self.subject), header_charset)

        with SMTP() as smtp:
            smtp.connect(self.smtp)
            smtp.sendmail(self.sender, self.recipient, msg.as_string())
