# Import smtplib for the actual sending function
import smtplib

# Here are the email package modules we'll need
from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mimetypes
import getpass

import os

def prompt(prompt):
    return raw_input(prompt).strip()

class MailSender:
    def __init__(self, mailServerDomain, mailServerPort):
        self.mailServerDomain = mailServerDomain
        self.mailServerPort = mailServerPort
        self.mailServer = None
        self.fromAddress = None
        self.toAddress = None
        self.subject = None
        self.content = None
        
    # adapted from https://docs.python.org/2/library/email-examples.html#email-examples
    def buildMime(self, filename):
            path = filename
            if not os.path.isfile(path):
                print filename + " is invalid"
                return None
            ctype, encoding = mimetypes.guess_type(path)
            if ctype is None or encoding is not None:
                # No guess could be made, or the file is encoded (compressed), so
                # use a generic bag-of-bits type.
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)
            if maintype == 'text':
                fp = open(path)
                # Note: we should handle calculating the charset
                msg = MIMEText(fp.read(), _subtype=subtype)
                fp.close()
            elif maintype == 'image':
                fp = open(path, 'rb')
                msg = MIMEImage(fp.read(), _subtype=subtype)
                fp.close()
            elif maintype == 'audio':
                fp = open(path, 'rb')
                msg = MIMEAudio(fp.read(), _subtype=subtype)
                fp.close()
            else:
                fp = open(path, 'rb')
                msg = MIMEBase(maintype, subtype)
                msg.set_payload(fp.read())
                fp.close()
                # Encode the payload using Base64
                encoders.encode_base64(msg)
            msg.add_header('Content-Disposition', 'attachment', filename="corrected_assignment")
            return msg

    def initSMTPSession(self, fqdn="anonymous", debug=1):
        # Send the email via our own SMTP server.
        #s = smtplib.SMTP('smtp.science.ru.nl',25)
        s = smtplib.SMTP(self.mailServerDomain, self.mailServerPort)  
        s.set_debuglevel(debug)
        s.ehlo(fqdn)
        s.starttls()
        s.ehlo(fqdn)
        s.login(prompt("Username: "), getpass.getpass("Password: "))
        self.smtpServer = s
    
    def setHeader(self, fromAddress = None, toAddress = None, content = None, subject = None):
        self.fromAddress = prompt("From Address: ") if fromAddress is None else fromAddress
        self.toAddress = prompt("Mail subject: ") if toAddress is None else toAddress
        self.subject = prompt("Mail subject:") if subject is None else subject
        if content is None:
            print "Content\n"
            self.content = ""
            while 1:
                try:
                    line = raw_input()
                except EOFError:
                    break
                if not line:
                    break
                self.content = self.content + line
            
    # Send the email via our own SMTP server.
    def sendPDF(self, pdfFile):
        # Check if all necessary options have been set
        if self.smtpServer is None:
            print "SMTP session not started (via setHeader method call)"
            return
        if self.fromAddress is None:
            print "Mail header not set (via setHeader method call)"
            return
            
        # Create the container (outer) email message.
        msg = MIMEMultipart()
        msg['Subject'] = self.subject
        msg['From'] = self.fromAddress
        msg['To'] = self.toAddress
        
        # Attach the pdf
        mime = self.buildMime(pdfFile)
        msg.attach(mime)
        self.smtpServer.sendmail(self.fromAddress, self.toAddress, msg.as_string())
        
    # Close session with server, the header is not cleared.
    def closeSMTPSession(self):
        if self.smtpServer is not None:
            self.smtpServer.quit()
            self.smtpServer = None

            
if __name__ == "__main__":
    sender = MailSender("smtp.science.ru.nl",25)
    sender.initSMTPSession()
    sender.setHeader()
    sender.sendPDF("img.pdf")
    sender.closeSMTPSession()