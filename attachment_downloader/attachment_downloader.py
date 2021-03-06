#!/usr/bin/env python

import logging
import os
import sys
from imbox import Imbox
from getpass import getpass
from optparse import OptionParser

from jinja2 import Template


def main():
    class InfoFilter(logging.Filter):
        def filter(self, rec):
            return rec.levelno in (logging.DEBUG, logging.INFO)


    std_out_stream_handler = logging.StreamHandler(sys.stdout)
    std_out_stream_handler.setLevel(logging.DEBUG)
    std_out_stream_handler.addFilter(InfoFilter())
    std_out_stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    std_err_stream_handler = logging.StreamHandler(sys.stderr)
    std_err_stream_handler.setLevel(logging.WARNING)
    std_err_stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(std_out_stream_handler)
    root_logger.addHandler(std_err_stream_handler)

    if sys.version_info[0] < 3:
        logging.error("This application requires Python 3+, you are running version: %s", sys.version)
        exit(1)

    parser = OptionParser()
    parser.add_option("--host", dest="host", help="IMAP Host")
    parser.add_option("--username", dest="username", help="IMAP Username")
    parser.add_option("--password", dest="password", help="IMAP Password")
    parser.add_option("--imap-folder", dest="imap_folder", help="IMAP Folder to extract attachments from")
    parser.add_option("--filename-template", dest="filename_template", help="Attachment filename (jinja2) template.",
                      default="{{ attachment_name }}")
    parser.add_option("--output", dest="download_folder", help="Output directory for attachment download")
    parser.add_option("--delete", dest="delete", action="store_true", help="Delete downloaed E-Mails from Mailbox")
    parser.add_option("--delete-copy-folder", dest="delete_copy_folder", help="IMAP folder to copy emails to before deleting them")

    (options, args) = parser.parse_args()

    if not options.host:
        parser.error('--host parameter required')
    if not options.username:
        parser.error('--username parameter required')
    if not options.imap_folder:
        parser.error('--folder parameter required')
    if not options.download_folder:
        parser.error('--output parameter required')
    if options.delete_copy_folder and not options.delete:
        parser.error('--delete parameter required when using --delete-copy-folder')

    password = options.password if options.password else getpass('IMAP Password: ')

    logging.info("Logging in to: '%s' as '%s'", options.host, options.username)
    mail = Imbox(options.host, username=options.username, password=options.password)

    logging.info("Listing messages in folder: %s", '"' + options.imap_folder + '"')
    messages = mail.messages(folder=options.imap_folder)

    for (uid, message) in messages:
        mail.mark_seen(uid)
        logging.info("Processing message '%s' subject '%s'", uid, message.subject)

        for idx, attachment in enumerate(message.attachments):
            try:
                filename_template = Template(options.filename_template)
                download_filename = filename_template.render(attachment_name=attachment.get('filename'),
                                                             attachment_idx=idx,
                                                             subject=message.subject,
                                                             message_id=message.message_id,
                                                             local_date=message.date)

                download_path = os.path.join(options.download_folder, download_filename)
                os.makedirs(os.path.dirname(os.path.abspath(download_path)), exist_ok=True)
                logging.info("Downloading attachment '%s' to path %s", attachment.get('filename'), download_path)

                if os.path.isfile(download_path):
                    logging.warning("Overwriting file: '%s'", download_path)

                with open(download_path, "wb") as fp:
                    fp.write(attachment.get('content').read())

            except Exception as e:
                logging.exception(e)
                logging.error('Error saving file. Continuing...')
            else:
                if options.delete:
                    if options.delete_copy_folder:
                        mail.copy(uid, '"' + options.delete_copy_folder + '"')

                    mail.delete(uid)



    logging.info('Finished processing messages')

    logging.info('Logging out of: %s', options.host)
    mail.logout()

    logging.info("Done")

if __name__ == '__main__':

    main()
