import requests
import configparser
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import pytz
import time
import os

py_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__))))


class BahaLogin:
    _session = None
    uid = ''
    password = ''
    scheduler_enable = False
    autosignin_time: datetime.datetime
    timezone = ''
    test_ok = False

    def __init__(self):
        if not self.read_setting():
            print('刪除 baha-autosignin.conf 可以重新產生設定檔')
            self.test_ok = False
            return

        print('測試登入')
        if not self.login():
            print('你的帳號密碼可能有錯誤，請檢查設定檔')
            self.test_ok = False
        else:
            self.test_ok = True

        if self.scheduler_enable:
            self.scheduler = BackgroundScheduler()
            self.scheduler.add_job(self.auto_sign, 'cron',
                                   hour=self.autosignin_time.hour,
                                   minute=self.autosignin_time.minute,
                                   second=self.autosignin_time.second,
                                   timezone=pytz.timezone(self.timezone))
            self.scheduler.start()

    def read_setting(self):
        setting_path = os.path.join(py_dir, 'baha-autosignin.conf')
        conf = configparser.ConfigParser()
        if not os.path.isfile(setting_path):
            conf.add_section('Account')
            conf.set('Account', 'id', '')
            conf.set('Account', 'password', '')
            conf.add_section('SelfBackgroundScheduler')
            conf.set('SelfBackgroundScheduler', 'enable', 'False')
            conf.set('SelfBackgroundScheduler', 'time', '3:0:0')
            conf.set('SelfBackgroundScheduler', 'timezone', 'Asia/Taipei')

            with open(setting_path, 'w', encoding='utf-8') as setting_file:
                conf.write(setting_file)
            print('第一次執行，請填寫 baha-autosignin.conf')
            return False
        else:
            conf.read(setting_path, encoding='utf-8')
            try:
                env_section = conf['Account']
                self.uid = env_section['id']
                self.password = env_section['password']
            except KeyError:
                print('讀取帳號失敗')
                return False
            try:
                self.scheduler_enable = conf.getboolean('SelfBackgroundScheduler', 'enable')
            except KeyError:
                print('讀取 SelfBackgroundScheduler 失敗.')
                self.scheduler_enable = False

            if self.scheduler_enable:
                try:
                    scheduler_session = conf['SelfBackgroundScheduler']
                    self.autosignin_time = datetime.datetime.strptime(scheduler_session['time'], '%H:%M:%S')
                    self.timezone = scheduler_session['timezone']
                except KeyError:
                    print('讀取 SelfBackgroundScheduler 失敗')
                    return False
        return True

    def signin_job(self):
        if self.scheduler_enable:
            while True:
                time.sleep(86400)
        else:
            self.auto_sign()

    def login(self):
        self._session = requests.session()
        self._session.headers.update(
            {
                'user-agent': 'Bahadroid (https://www.gamer.com.tw/)',
                'x-bahamut-app-instanceid': 'cc2zQIfDpg4',
                'x-bahamut-app-android': 'tw.com.gamer.android.activecenter',
                'x-bahamut-app-version': '251',
                'content-type': 'application/x-www-form-urlencoded',
                'content-length': '44',
                'accept-encoding': 'gzip',
                'cookie': 'ckAPP_VCODE=7045'
            },
        )

        account = self._session.post('https://api.gamer.com.tw/mobile_app/user/v3/do_login.php'
                                     , data={'uid': self.uid, 'passwd': self.password, 'vcode': '7045'})
        account_f = account.json()
        if 'success' in account_f and account_f['success']:
            print('登入成功!')
            self._session.headers = {
                'user-agent': 'Bahadroid (https://www.gamer.com.tw/)',
                'x-bahamut-app-instanceid': 'cc2zQIfDpg4',
                'x-bahamut-app-android': 'tw.com.gamer.android.activecenter',
                'x-bahamut-app-version': '251',
                'accept-encoding': 'gzip'
            }

            """
            print('[Info]您好：{}'.format(account_f['nickname']))
            print('[-----勇者資訊如下-----]')
            print('[Info]等級：{}'.format(account_f['lv']))
            print('[Info]ＧＰ：{}'.format(account_f['gp']))
            print('[Info]巴幣：{}'.format(account_f['gold']))
            """

            return True
        else:
            print('登入失敗!')
            return False

    def auto_sign(self):
        sign_info = self._session.post('https://www.gamer.com.tw/ajax/signin.php', data={'action': '2'}).json()
        # print(sign_info)
        if sign_info['data']['signin'] == 1:
            print('已經簽到過了')
        else:
            token = self._session.get(
                'https://www.gamer.com.tw/ajax/get_csrf_token.php').text
            json_info = self._session.post(
                'https://www.gamer.com.tw/ajax/signin.php', data={'action': '1', 'token': token})
            json_info = json_info.json()
            print(json_info)
            if 'data' in json_info:
                print(f'巴哈姆特自動簽到成功!!')
            else:
                print('簽到失敗')
                return False

        sign_info = self._session.post('https://www.gamer.com.tw/ajax/signin.php', data={'action': '2'}).json()
        print('每日連續簽到 ', sign_info['data']['days'], '天')
        print('週年慶連續簽到 ', sign_info['data']['prjSigninDays'], ' 天')

        return True


if __name__ == '__main__':
    b_login = BahaLogin()
    if b_login.test_ok:
        b_login.signin_job()



