import logging
from threading import Thread
from flask import current_app, render_template
from flask_mail import Message

from app.extensions import mail


class MailService:
    def _send_async_email(self, app, msg, code_for_log=None):
        with app.app_context():
            try:
                # Only log 2FA code if explicitly enabled via config
                if code_for_log and app.config.get('ENABLE_2FA_CODE_LOGGING', False):
                    logging.info(f"[DEV] 2FA code for {msg.recipients}: {code_for_log}")

                mail.send(msg)
                logging.info(f"Email sent successfully to {msg.recipients}")
            except Exception as e:
                logging.error(f"CRITICAL: Failed to send email to {msg.recipients}: {str(e)}")

    def send_email(self, subject, recipients, template, code_for_log=None, sync=False, attachments=None, **kwargs):
        app = current_app._get_current_object()
        msg = Message(subject, recipients=recipients)
        msg.html = render_template(template, **kwargs)

        if attachments:
            for att in attachments:
                msg.attach(
                    filename=att['filename'],
                    content_type=att['content_type'],
                    data=att['data']
                )

        if sync or app.debug:
            self._send_async_email(app, msg, code_for_log)
        else:
            thr = Thread(target=self._send_async_email, args=(app, msg, code_for_log))
            thr.start()

    def send_admin_2fa_code(self, user, code):
        try:
            self.send_email(
                subject="Código de Verificación - Admin Panel",
                recipients=[user.email],
                template='emails/admin_2fa_code.html',
                code_for_log=code,
                code=code,
                user=user
            )
        except Exception as e:
            logging.error(f"Error preparing 2FA email: {e}")


mail_service = MailService()


def send_2fa_email(to_email, code):
    mail_service.send_email(
        subject="[Admin Panel] Código de Verificación",
        recipients=[to_email],
        template='emails/admin_2fa_code.html',
        code_for_log=code,
        code=code
    )