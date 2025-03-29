import datetime

from engines.engine import Sender, job_engine
from models.signal import Signal
from models.review import Review
import smtplib
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def email(subject, body):
    try:
        smtp_server = "smtp.163.com"
        smtp_username = "itishsy@163.com"
        smtp_password = "KSEJTXDLZLXNBMMI"
        smtp = smtplib.SMTP(smtp_server, port=25)
        smtp.starttls()
        smtp.login(smtp_username, smtp_password)
        from_email = "itishsy@163.com"
        to_email = "279440948@qq.com"
        message = MIMEMultipart()
        message["From"] = "itishsy@163.com"
        message["To"] = "279440948@qq.com"
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain", "utf-8"))
        # subject = subject
        # body = body.encode('utf-8')
        # message = f"From: {from_email}\nTo: {to_email}\nSubject: {subject}\n\n{body}"
        smtp.sendmail(from_email, to_email, message.as_string())
        smtp.quit()
        return True
    except Exception as e:
        traceback.print_exc()
        return False


@job_engine
class SignalNotify(Sender):

    def send(self):
        sis = Signal.select().where(Signal.notify == 0)
        msg = ''
        for si in sis:
            if si.code.startswith('60'):
                msg = msg + "http://xueqiu.com/S/SH{} {},{},{} ".format(si.code, si.dt, si.freq, si.strategy)
            else:
                msg = msg + "http://xueqiu.com/S/SZ{} {},{},{} ".format(si.code, si.dt, si.freq, si.strategy)

        if msg != '':
            if email('Signal', msg):
                for si in sis:
                    si.notify = 1
                    si.updated = datetime.datetime.now()
                    si.save()
                return True
            return False


@job_engine
class ReviewNotify(Sender):

    def send(self):
        review = Review.select().order_by(Review.created.desc()).get()
        content = ('【大盘表现】\n {} \n {} \n {} \n'
                   '--------------------------------------------------'
                   '\n【板块资金流动】\n {} \n {} \n'
                   '--------------------------------------------------'
                   '\n【热门板块】 \n {} \n {} \n'
                   '--------------------------------------------------'
                   '\n 【热门个股】 \n{}').format(
            review.pan_data, review.pan_summary, review.pan_focus, review.bk_in, review.bk_out,
            review.bk_fk, review.bk_ql, review.gp_hot1)
        email('Review', content)
