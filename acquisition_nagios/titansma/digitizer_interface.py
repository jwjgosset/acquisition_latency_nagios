import http
import os
import hashlib
import http.cookiejar
import urllib.request
import urllib


class GlobalCookieJar:
    def __init__(
        self,
        filename=None
    ):
        self.cookiejar = http.cookiejar.MozillaCookieJar(filename)
        if filename is not None and os.path.exists(filename):
            self.cookiejar.load(ignore_discard=True)

    def addCookieToJar(
        self,
        response: http.client.HTTPResponse,
        request: urllib.request.Request
    ):
        self.cookiejar.extract_cookies(response, request)
        if self.cookiejar.filename is not None:
            self.cookiejar.save(ignore_discard=True)

    def addCookieToAllRequests(self):
        urllib.request.install_opener(
            urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(self.cookiejar)))
        return self

    def addCookieToRequest(
        self,
        request: urllib.request.Request
    ):
        self.cookiejar.add_cookie_header(request)
        return self


def getHash(
    string: str
) -> str:
    return hashlib.md5(bytearray(string, 'ascii')).hexdigest()


class DigitizerInterface:
    def __init__(
        self,
        address: str,
        username: str,
        password: str
    ):
        self.address = address
        self.username = username
        self.password = password

    def getUrl(
        self,
        relative: str
    ) -> str:
        return 'http://' + self.address + relative

    def getKey(
        self,
        cookiejar: GlobalCookieJar
    ):
        request = urllib.request.Request(self.getUrl('/key'))
        response = urllib.request.urlopen(request)
        cookiejar.addCookieToJar(response, request)
        return response.read().decode('ascii')

    def login(self, cookiejar):
        key = self.getKey(cookiejar)
        encodedPassword = getHash(getHash(self.password) + key)

        request = urllib.request.Request(self.getUrl('/login'), method='POST')
        request.add_header('X-NMX-USERNAME', self.username)
        request.add_header('X-NMX-PASSWORD', encodedPassword)
        urllib.request.urlopen(request)

    def getConfiguration(self):
        request = urllib.request.Request(self.getUrl('/config'))
        try:
            response = urllib.request.urlopen(request)
        except urllib.error.HTTPError as e:
            print(e)
        return response.read().decode()
